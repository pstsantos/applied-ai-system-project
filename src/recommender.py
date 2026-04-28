from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        """Initialise the recommender with a catalog of Song objects."""
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects best matching the given UserProfile."""
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language string explaining why song was recommended for user."""
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, str]:
    """
    Scores a single song against user preferences.
    Returns (score, explanation) where explanation breaks down each contribution.
    """
    reasons = []

    # --- P1: Mood match (0.17) ---
    if song["mood"] in user_prefs["mood"]:
        mood_score = 0.17
        reasons.append(f"mood match — {song['mood']} (+{mood_score:.2f})")
    else:
        mood_score = 0.0

    # --- P1: Genre match (0.13) ---
    if song["genre"] in user_prefs["genre"]:
        genre_score = 0.13
        reasons.append(f"genre match — {song['genre']} (+{genre_score:.2f})")
    else:
        genre_score = 0.0

    # --- P2: Energy distance (0.175) ---
    energy_score = 0.175 * (1 - abs(song["energy"] - user_prefs["target_energy"]))
    reasons.append(f"energy fit (+{energy_score:.2f})")

    # --- P2: Valence distance (0.175) ---
    valence_score = 0.175 * (1 - abs(song["valence"] - user_prefs["target_valence"]))
    reasons.append(f"valence fit (+{valence_score:.2f})")

    # --- P3: Danceability distance (0.15) ---
    dance_score = 0.15 * (1 - abs(song["danceability"] - user_prefs["target_danceability"]))
    reasons.append(f"danceability fit (+{dance_score:.2f})")

    # --- P3: Tempo distance (0.15), normalised to 0-1 over 60-200 BPM range ---
    tempo_norm = (song["tempo_bpm"] - 60) / (200 - 60)
    target_tempo_norm = (user_prefs["target_tempo_bpm"] - 60) / (200 - 60)
    tempo_score = 0.15 * (1 - abs(tempo_norm - target_tempo_norm))
    reasons.append(f"tempo fit (+{tempo_score:.2f})")

    # --- Acoustic penalty (up to -0.10) ---
    acoustic_penalty = 0.0
    if not user_prefs["likes_acoustic"]:
        acoustic_penalty = song["acousticness"] * 0.10
        if acoustic_penalty > 0.01:
            reasons.append(f"acoustic penalty (-{acoustic_penalty:.2f})")

    score = mood_score + genre_score + energy_score + valence_score + dance_score + tempo_score - acoustic_penalty
    explanation = " · ".join(reasons)

    return round(score, 4), explanation


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    import csv
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": float(row["tempo_bpm"]),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    print(f"Loaded {len(songs)} songs.")
    return songs

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, exclude_ids: Optional[List[int]] = None) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    # Filter out already-heard songs
    if exclude_ids:
        songs = [s for s in songs if s["id"] not in exclude_ids]

    # Score every song and sort descending by score, tie-break by valence
    scored = sorted(
        ((song, *score_song(user_prefs, song)) for song in songs),
        key=lambda x: (x[1], x[0]["valence"]),
        reverse=True
    )

    # Diversity: max 2 songs per artist
    results = []
    artist_counts: Dict[str, int] = {}
    for song, score, explanation in scored:
        count = artist_counts.get(song["artist"], 0)
        if count < 2:
            results.append((song, score, explanation))
            artist_counts[song["artist"]] = count + 1
        if len(results) >= k:
            break

    return results
