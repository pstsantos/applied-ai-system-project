import pandas as pd

from src.load_kaggle import append_to_existing_catalog, transform_source_frame


def test_transform_source_frame_filters_and_normalizes_rows():
    source = pd.DataFrame(
        [
            {
                "track_id": "pop-1",
                "track_name": "Bright Track",
                "artists": "Artist One;Artist Two",
                "popularity": 90,
                "track_genre": "pop",
                "danceability": 0.81,
                "energy": 0.88,
                "speechiness": 0.04,
                "acousticness": 0.12,
                "instrumentalness": 0.0,
                "valence": 0.84,
                "tempo": 210.2,
            },
            {
                "track_id": "skip-1",
                "track_name": "Skip Me",
                "artists": "Unknown",
                "popularity": 10,
                "track_genre": "classical",
                "danceability": 0.2,
                "energy": 0.1,
                "speechiness": 0.03,
                "acousticness": 0.95,
                "instrumentalness": 0.85,
                "valence": 0.2,
                "tempo": 55.0,
            },
        ]
    )

    result = transform_source_frame(source)

    assert len(result) == 1
    assert result.iloc[0].to_dict() == {
        "title": "Bright Track",
        "artist": "Artist One, Artist Two",
        "genre": "pop",
        "mood": "intense",
        "energy": 0.88,
        "tempo_bpm": 200,
        "valence": 0.84,
        "danceability": 0.81,
        "acousticness": 0.12,
    }


def test_append_to_existing_catalog_keeps_seed_rows_and_dedupes_new_rows(tmp_path):
    output_path = tmp_path / "songs.csv"
    existing = pd.DataFrame(
        [
            {
                "id": 1,
                "title": "Seed Song",
                "artist": "Seed Artist",
                "genre": "pop",
                "mood": "happy",
                "energy": 0.7,
                "tempo_bpm": 120,
                "valence": 0.8,
                "danceability": 0.75,
                "acousticness": 0.1,
            }
        ]
    )
    existing.to_csv(output_path, index=False)

    imported = pd.DataFrame(
        [
            {
                "title": "Seed Song",
                "artist": "Seed Artist",
                "genre": "pop",
                "mood": "happy",
                "energy": 0.7,
                "tempo_bpm": 120,
                "valence": 0.8,
                "danceability": 0.75,
                "acousticness": 0.1,
            },
            {
                "title": "New Song",
                "artist": "New Artist",
                "genre": "rock",
                "mood": "intense",
                "energy": 0.9,
                "tempo_bpm": 150,
                "valence": 0.4,
                "danceability": 0.6,
                "acousticness": 0.05,
            },
        ]
    )

    merged = append_to_existing_catalog(imported, output_path, replace=False)

    assert merged["id"].tolist() == [1, 2]
    assert merged[["title", "artist"]].values.tolist() == [
        ["Seed Song", "Seed Artist"],
        ["New Song", "New Artist"],
    ]
