"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Taste profile — keys match the scoring tiers in the README:
    # P1: genre, mood  |  P2: energy, valence  |  P3: danceability, tempo_bpm
    user_prefs = {
        "genre": ["rap"],        # P1 — similar genres treated as equal matches
        "mood": ["happy", "intense"],       # P1 — emotionally close moods grouped together
        "target_energy": 0.50,               # P2 — how energetic the song should feel
        "target_valence": 0.50,              # P2 — how positive/upbeat the song should feel
        "target_danceability": 0.30,         # P3 — how danceable
        "target_tempo_bpm": 120,             # P3 — preferred tempo
        "likes_acoustic": False,             # penalises high acousticness songs
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\n" + "=" * 50)
    print(f"  Top {len(recommendations)} Recommendations for You")
    print("=" * 50)

    for i, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n#{i}  {song['title']} — {song['artist']}")
        print(f"    Genre: {song['genre']}  |  Mood: {song['mood']}")
        print(f"    Score: {score:.2f}")
        print(f"    Why:   {explanation}")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
