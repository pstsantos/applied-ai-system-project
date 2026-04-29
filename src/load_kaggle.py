"""
Build Aura's song catalog from the Spotify tracks dataset.

The app expects a narrow schema:
id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness

The Kaggle source has richer Spotify audio features plus many more raw genres.
This loader normalizes the dataset into Aura's closed vocabulary so the rest of
the app can keep using the same recommender and UI controls.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import get_args

import pandas as pd

from src.schema import GENRES, MOODS

RAW_TO_AURA_GENRE = {
    "pop": "pop",
    "power-pop": "pop",
    "pop-film": "pop",
    "k-pop": "pop",
    "j-pop": "pop",
    "mandopop": "pop",
    "cantopop": "pop",
    "indie-pop": "indie pop",
    "indie": "indie pop",
    "rock": "rock",
    "alt-rock": "rock",
    "hard-rock": "rock",
    "j-rock": "rock",
    "psych-rock": "rock",
    "punk-rock": "rock",
    "rock-n-roll": "rock",
    "rockabilly": "rock",
    "hip-hop": "rap",
    "study": "lofi",
    "chill": "lofi",
    "jazz": "jazz",
    "ambient": "ambient",
    "new-age": "ambient",
    "synth-pop": "synthwave",
}

OUTPUT_COLUMNS = [
    "id",
    "title",
    "artist",
    "genre",
    "mood",
    "energy",
    "tempo_bpm",
    "valence",
    "danceability",
    "acousticness",
]


def export_numbers_to_csv(source: Path, target: Path) -> None:
    """Export a Numbers workbook to CSV using the native macOS Numbers app."""
    if sys.platform != "darwin":
        raise RuntimeError("`.numbers` import currently requires macOS and Numbers.app.")
    if shutil.which("osascript") is None:
        raise RuntimeError("`osascript` is not available; cannot export `.numbers` file.")

    source = source.resolve()
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()

    script = [
        'tell application "Numbers"',
        f'set docRef to open POSIX file "{source}"',
        f'export docRef to POSIX file "{target}" as CSV',
        "close docRef saving no",
        "end tell",
    ]

    cmd = ["osascript"]
    for line in script:
        cmd.extend(["-e", line])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise RuntimeError(f"Numbers export failed: {stderr}") from exc


def load_source_frame(source: Path) -> pd.DataFrame:
    """Load either a CSV export or a Numbers workbook into a DataFrame."""
    suffix = source.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(source)

    if suffix == ".numbers":
        with tempfile.TemporaryDirectory(prefix="aura_numbers_export_") as tmpdir:
            export_path = Path(tmpdir) / f"{source.stem}.csv"
            export_numbers_to_csv(source, export_path)
            return pd.read_csv(export_path)

    raise ValueError(f"Unsupported source type: {source.suffix}")


def infer_mood(row: pd.Series) -> str:
    """Map Spotify audio features onto Aura's fixed mood labels."""
    energy = float(row["energy"])
    valence = float(row["valence"])
    tempo = float(row["tempo"])
    danceability = float(row["danceability"])
    acousticness = float(row["acousticness"])
    instrumentalness = float(row["instrumentalness"])
    speechiness = float(row["speechiness"])
    genre = str(row["genre"])

    if energy >= 0.82 and tempo >= 125:
        return "intense"
    if energy >= 0.70 and tempo >= 138 and danceability <= 0.58:
        return "epic"
    if valence >= 0.72 and energy >= 0.45:
        return "happy"

    if genre in {"ambient", "lofi"}:
        if energy < 0.38 and valence >= 0.55:
            return "relaxed"
        if speechiness <= 0.06 and (instrumentalness >= 0.15 or acousticness >= 0.45) and energy <= 0.58:
            return "focused"

    if valence < 0.28 and energy < 0.62:
        return "melancholic"
    if energy < 0.35 and valence >= 0.55:
        return "relaxed"
    if instrumentalness >= 0.72:
        return "focused"
    if acousticness >= 0.58 and 70 <= tempo <= 125 and 0.22 <= valence <= 0.58:
        return "nostalgic"
    if valence < 0.45 and energy < 0.72:
        return "moody"
    if 0.45 <= valence < 0.72 and energy >= 0.58:
        return "passionate"
    return "chill"


def transform_source_frame(source_df: pd.DataFrame) -> pd.DataFrame:
    """Filter, map, dedupe, and normalize Spotify rows into Aura's schema."""
    df = source_df.copy()
    df = df[df["track_genre"].isin(RAW_TO_AURA_GENRE)].copy()
    df["genre"] = df["track_genre"].map(RAW_TO_AURA_GENRE)

    # Keep the most popular copy of duplicated tracks before projecting columns.
    df = df.sort_values(
        ["popularity", "track_name", "artists"],
        ascending=[False, True, True],
    )
    df = df.drop_duplicates(subset=["track_id"])
    df = df.drop_duplicates(subset=["track_name", "artists"])

    df["mood"] = df.apply(infer_mood, axis=1)

    catalog = pd.DataFrame(
        {
            "title": df["track_name"].astype(str).str.strip(),
            "artist": df["artists"].astype(str).str.replace(";", ", ", regex=False).str.strip(),
            "genre": df["genre"],
            "mood": df["mood"],
            "energy": df["energy"].clip(0.0, 1.0).round(4),
            "tempo_bpm": df["tempo"].clip(60, 200).round().astype(int),
            "valence": df["valence"].clip(0.0, 1.0).round(4),
            "danceability": df["danceability"].clip(0.0, 1.0).round(4),
            "acousticness": df["acousticness"].clip(0.0, 1.0).round(4),
        }
    )

    catalog = catalog.dropna().copy()
    catalog = catalog[catalog["title"] != ""]
    catalog = catalog[catalog["artist"] != ""]
    return catalog.reset_index(drop=True)


def append_to_existing_catalog(imported_df: pd.DataFrame, output_path: Path, replace: bool) -> pd.DataFrame:
    """Merge imported rows into the existing catalog and assign sequential IDs."""
    if replace or not output_path.exists():
        existing = pd.DataFrame(columns=OUTPUT_COLUMNS)
    else:
        existing = pd.read_csv(output_path)

    if existing.empty:
        merged = imported_df.copy()
    else:
        existing_keys = set(
            zip(
                existing["title"].astype(str).str.casefold(),
                existing["artist"].astype(str).str.casefold(),
            )
        )
        imported = imported_df.copy()
        imported_keys = list(
            zip(
                imported["title"].astype(str).str.casefold(),
                imported["artist"].astype(str).str.casefold(),
            )
        )
        imported = imported.loc[[key not in existing_keys for key in imported_keys]].copy()
        merged = pd.concat([existing[OUTPUT_COLUMNS[1:]], imported], ignore_index=True)

    merged.insert(0, "id", range(1, len(merged) + 1))
    return merged[OUTPUT_COLUMNS]


def validate_catalog(df: pd.DataFrame) -> None:
    """Ensure the generated catalog still matches the app's closed vocabulary."""
    allowed_genres = set(get_args(GENRES))
    allowed_moods = set(get_args(MOODS))

    invalid_genres = sorted(set(df["genre"]) - allowed_genres)
    invalid_moods = sorted(set(df["mood"]) - allowed_moods)

    if invalid_genres:
        raise ValueError(f"Unexpected genres in generated catalog: {invalid_genres}")
    if invalid_moods:
        raise ValueError(f"Unexpected moods in generated catalog: {invalid_moods}")


def build_catalog(source: Path, output: Path, replace: bool = False) -> pd.DataFrame:
    """Load the raw dataset, normalize it, merge it, and write songs.csv."""
    source_df = load_source_frame(source)
    imported_df = transform_source_frame(source_df)
    final_df = append_to_existing_catalog(imported_df, output, replace=replace)
    validate_catalog(final_df)
    output.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output, index=False)
    return final_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize the Spotify dataset into Aura's songs.csv schema.")
    parser.add_argument("source", type=Path, help="Path to a .csv or .numbers Spotify dataset export.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/songs.csv"),
        help="Destination CSV path. Defaults to data/songs.csv.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace the output catalog instead of appending to the existing songs.csv.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalog = build_catalog(args.source, args.output, replace=args.replace)
    print(f"Wrote {len(catalog)} rows to {args.output}")


if __name__ == "__main__":
    main()
