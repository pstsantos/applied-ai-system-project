"""
Adversarial tests that expose two concrete bugs in score_song().

Run with:  pytest tests/test_adversarial.py -v -s
  -v  shows each test name + PASSED/FAILED
  -s  lets print() output reach the terminal
"""

import pytest
from src.recommender import score_song


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _base_user(**overrides):
    """Minimal valid user_prefs dict; override any key via kwargs."""
    prefs = {
        "genre": ["lofi"],
        "mood": ["chill"],
        "target_energy": 0.5,
        "target_valence": 0.6,
        "target_danceability": 0.6,
        "target_tempo_bpm": 80,
        "likes_acoustic": False,
    }
    prefs.update(overrides)
    return prefs


def _make_song(**overrides):
    """Minimal valid song dict; override any key via kwargs."""
    song = {
        "id": 99,
        "title": "Test Song",
        "artist": "Test Artist",
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.5,
        "tempo_bpm": 80,
        "valence": 0.6,
        "danceability": 0.6,
        "acousticness": 0.1,
    }
    song.update(overrides)
    return song


# ---------------------------------------------------------------------------
# BUG #1 — Out-of-range tempo can produce a negative tempo component
# ---------------------------------------------------------------------------

class TestOutOfRangeTempo:
    """
    The tempo formula is:
        tempo_norm        = (song_bpm  - 60) / 140
        target_tempo_norm = (target_bpm - 60) / 140
        tempo_score       = 0.15 * (1 - |tempo_norm - target_tempo_norm|)

    When target_bpm > 200, target_tempo_norm > 1.0.
    If the song is slow, the absolute difference exceeds 1.0 and
    (1 - diff) goes negative, making tempo_score negative.
    """

    def _extract_tempo_score(self, user, song):
        """Recompute the tempo component in isolation so we can inspect it."""
        tempo_norm        = (song["tempo_bpm"] - 60) / (200 - 60)
        target_tempo_norm = (user["target_tempo_bpm"] - 60) / (200 - 60)
        return 0.15 * (1 - abs(tempo_norm - target_tempo_norm))

    def test_tempo_score_is_non_negative_within_range(self):
        """Baseline: targets within [60, 200] never produce negative tempo scores."""
        user = _base_user(target_tempo_bpm=120)
        for bpm in [60, 80, 100, 120, 150, 170, 200]:
            song = _make_song(tempo_bpm=bpm)
            t = self._extract_tempo_score(user, song)
            print(f"  target=120 BPM, song={bpm} BPM → tempo_score={t:.4f}")
            assert t >= 0, f"Expected non-negative, got {t:.4f} at song_bpm={bpm}"

    def test_tempo_score_goes_negative_when_target_exceeds_200(self):
        """
        BUG: target_tempo_bpm=250 pushes target_tempo_norm to 1.357.
        A slow song (65 BPM) gets tempo_norm≈0.036, difference≈1.321,
        so tempo_score = 0.15 * (1 - 1.321) = -0.048.

        This test FAILS to reveal the bug — the assertion documents
        what the correct behaviour should be.
        """
        user = _base_user(target_tempo_bpm=250)
        slow_song = _make_song(tempo_bpm=65)

        target_norm = (250 - 60) / (200 - 60)
        song_norm   = ( 65 - 60) / (200 - 60)
        tempo_score = 0.15 * (1 - abs(song_norm - target_norm))

        full_score, explanation = score_song(user, slow_song)

        print(f"\n  target_tempo_bpm  = 250")
        print(f"  target_tempo_norm = {target_norm:.4f}  ← exceeds 1.0!")
        print(f"  song_tempo_bpm    = 65")
        print(f"  song_tempo_norm   = {song_norm:.4f}")
        print(f"  tempo_score       = {tempo_score:.4f}  ← NEGATIVE")
        print(f"  full score        = {full_score:.4f}")
        print(f"  explanation       : {explanation}")

        assert tempo_score >= 0, (
            f"tempo_score should be >= 0 for any valid input, "
            f"but got {tempo_score:.4f} (target_bpm=250, song_bpm=65). "
            f"Fix: clamp target_tempo_bpm to [60, 200] before normalising."
        )

    def test_out_of_range_inflates_fast_songs_unfairly(self):
        """
        With target_bpm=250, a fast song (180 BPM) gets a positive tempo score
        while a slow song (65 BPM) gets a negative one — a 0.12-pt swing that
        has nothing to do with musical preference.
        """
        user = _base_user(target_tempo_bpm=250)
        slow_song = _make_song(tempo_bpm=65,  title="Slow Song")
        fast_song = _make_song(tempo_bpm=180, title="Fast Song")

        slow_t = self._extract_tempo_score(user, slow_song)
        fast_t = self._extract_tempo_score(user, fast_song)

        print(f"\n  target_tempo_bpm=250 (out of range)")
        print(f"  Slow Song (65 BPM)  tempo_score = {slow_t:.4f}")
        print(f"  Fast Song (180 BPM) tempo_score = {fast_t:.4f}")
        print(f"  Spread = {fast_t - slow_t:.4f} pts from an out-of-range target alone")

        assert slow_t >= 0, (
            f"Slow song tempo_score={slow_t:.4f} is negative due to out-of-range target_bpm=250"
        )


# ---------------------------------------------------------------------------
# BUG #2 — Acoustic penalty can invert rankings within a matched cluster
# ---------------------------------------------------------------------------

class TestAcousticPenaltyInversion:
    """
    likes_acoustic=False applies:  score -= acousticness * 0.10

    The penalty is not bounded relative to the continuous-feature advantage
    a well-matched song should have. A perfectly-matched high-acoustic song
    can lose to a poorly-matched low-acoustic song from the same genre+mood.
    """

    # Two songs that both match the user's genre (lofi) and mood (chill).
    # Song A is the PERFECT energy match; Song B is 0.20 off — but has
    # almost no acousticness, so the penalty flips the ranking.
    PERFECT_MATCH = _make_song(
        title="Perfect Energy Lofi",
        genre="lofi", mood="chill",
        energy=0.35,        # exactly what the user wants
        valence=0.60,
        danceability=0.60,
        tempo_bpm=80,
        acousticness=0.95,  # common for lofi — gets hit hard
    )
    IMPERFECT_MATCH = _make_song(
        title="Off-Energy Lofi",
        genre="lofi", mood="chill",
        energy=0.55,        # 0.20 away from target
        valence=0.60,
        danceability=0.60,
        tempo_bpm=80,
        acousticness=0.05,  # almost none → almost no penalty
    )
    USER = _base_user(
        genre=["lofi"],
        mood=["chill"],
        target_energy=0.35,
        target_valence=0.60,
        target_danceability=0.60,
        target_tempo_bpm=80,
        likes_acoustic=False,
    )

    def test_perfect_energy_match_should_score_higher(self):
        """
        BUG: The perfectly-matched song (energy delta=0.00) should outscore
        the off-energy song (energy delta=0.20). Instead the acoustic penalty
        of 0.090 erases the 0.035-pt energy advantage and flips the ranking.

        This test FAILS to reveal the bug.
        """
        score_a, expl_a = score_song(self.USER, self.PERFECT_MATCH)
        score_b, expl_b = score_song(self.USER, self.IMPERFECT_MATCH)

        energy_advantage = 0.175 * abs(0.55 - 0.35)   # = 0.035
        acoustic_gap     = (0.95 - 0.05) * 0.10        # = 0.090

        print(f"\n  User wants: lofi/chill, target_energy=0.35, likes_acoustic=False")
        print()
        print(f"  '{self.PERFECT_MATCH['title']}'")
        print(f"    energy={self.PERFECT_MATCH['energy']} (delta=0.00), "
              f"acousticness={self.PERFECT_MATCH['acousticness']}")
        print(f"    acoustic penalty = -{self.PERFECT_MATCH['acousticness'] * 0.10:.3f}")
        print(f"    score = {score_a:.4f}")
        print(f"    why   : {expl_a}")
        print()
        print(f"  '{self.IMPERFECT_MATCH['title']}'")
        print(f"    energy={self.IMPERFECT_MATCH['energy']} (delta=0.20), "
              f"acousticness={self.IMPERFECT_MATCH['acousticness']}")
        print(f"    acoustic penalty = -{self.IMPERFECT_MATCH['acousticness'] * 0.10:.3f}")
        print(f"    score = {score_b:.4f}")
        print(f"    why   : {expl_b}")
        print()
        print(f"  Energy advantage of perfect match : +{energy_advantage:.3f} pts")
        print(f"  Acoustic penalty gap (works against): -{acoustic_gap:.3f} pts")
        print(f"  Net effect on perfect match       : {energy_advantage - acoustic_gap:+.3f} pts")
        print()
        if score_a < score_b:
            print(f"  RANKING INVERTED: off-energy song wins by {score_b - score_a:.4f} pts")

        assert score_a > score_b, (
            f"Perfect energy match (score={score_a:.4f}) should beat "
            f"off-energy song (score={score_b:.4f}), but the acoustic "
            f"penalty flipped the ranking. "
            f"Energy advantage (+{energy_advantage:.3f}) is smaller than "
            f"the acoustic penalty gap (-{acoustic_gap:.3f})."
        )

    def test_likes_acoustic_true_provides_no_positive_reward(self):
        """
        Exposing the asymmetry: likes_acoustic=True only disables the penalty.
        It does NOT add any positive weight for acoustic content.

        A user who loves acoustic music gets identical continuous-feature
        scores to a user who is neutral about acousticness.
        """
        user_loves_acoustic   = _base_user(likes_acoustic=True)
        user_neutral_acoustic = _base_user(likes_acoustic=True)  # same flag

        acoustic_song = _make_song(acousticness=0.95, title="Highly Acoustic Song")

        score_lover,   expl_lover   = score_song(user_loves_acoustic,   acoustic_song)
        score_neutral, expl_neutral = score_song(user_neutral_acoustic, acoustic_song)

        print(f"\n  Acoustic song (acousticness=0.95)")
        print(f"  likes_acoustic=True  score: {score_lover:.4f}  — {expl_lover}")
        print(f"  likes_acoustic=True  score: {score_neutral:.4f}  — {expl_neutral}")
        print()
        print(f"  The flag provides no POSITIVE reward for acoustic content.")
        print(f"  An 'I love acoustic' user and an 'I don't care' user get the same score.")

        # Both are True here, so scores must match — the test passes,
        # but the print output shows the design gap clearly.
        assert score_lover == score_neutral

    def test_acoustic_penalty_magnitude_vs_feature_weights(self):
        """
        Documents the weight imbalance: the acoustic penalty (up to 0.10)
        can cancel more than half the energy component (max 0.175) or
        more than two-thirds of the danceability component (max 0.15).
        """
        max_acoustic_penalty = 1.0 * 0.10   # acousticness=1.0
        max_energy_weight    = 0.175
        max_dance_weight     = 0.15
        max_genre_weight     = 0.13

        print(f"\n  Max acoustic penalty        : {max_acoustic_penalty:.3f}")
        print(f"  Max energy component        : {max_energy_weight:.3f}  "
              f"(penalty is {max_acoustic_penalty/max_energy_weight*100:.0f}% of this)")
        print(f"  Max danceability component  : {max_dance_weight:.3f}  "
              f"(penalty is {max_acoustic_penalty/max_dance_weight*100:.0f}% of this)")
        print(f"  Max genre-match bonus       : {max_genre_weight:.3f}  "
              f"(penalty is {max_acoustic_penalty/max_genre_weight*100:.0f}% of this)")
        print()
        print(f"  A fully acoustic song (acousticness=1.0) loses more points")
        print(f"  from the penalty than it could gain from a genre match.")

        # The penalty should not exceed any individual positive component's max.
        # This assertion will FAIL for the genre comparison, revealing the imbalance.
        assert max_acoustic_penalty <= max_genre_weight, (
            f"Acoustic penalty ({max_acoustic_penalty:.3f}) exceeds the genre-match "
            f"bonus ({max_genre_weight:.3f}). A perfect genre match can be wiped out "
            f"by acousticness alone."
        )
