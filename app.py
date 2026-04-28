import streamlit as st
from src.recommender import load_songs, recommend_songs

st.set_page_config(page_title="Aura", page_icon="🎧", layout="centered")

@st.cache_data
def get_songs():
    return load_songs("data/songs.csv")

songs = get_songs()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎧 Aura")
st.caption("Tell it what you're feeling. Get five songs back.")
st.divider()

# ── Preferences form ─────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    genres = st.multiselect(
        "Genres",
        ["pop", "indie pop", "rock", "rap", "lofi", "jazz", "ambient", "synthwave"],
        default=["pop"],
    )
    moods = st.multiselect(
        "Moods",
        ["happy", "chill", "intense", "focused", "nostalgic",
         "moody", "melancholic", "relaxed", "passionate", "epic"],
        default=["happy"],
    )
    likes_acoustic = st.toggle("I like acoustic music", value=False)

with col2:
    energy    = st.slider("Energy",       0.0, 1.0, 0.7, 0.05)
    valence   = st.slider("Positivity",   0.0, 1.0, 0.7, 0.05)
    dance     = st.slider("Danceability", 0.0, 1.0, 0.7, 0.05)
    tempo     = st.slider("Tempo (BPM)",  60,  200, 120, 5)

st.divider()

# ── Run recommender ───────────────────────────────────────────────────────────
if not genres or not moods:
    st.warning("Pick at least one genre and one mood.")
    st.stop()

user_prefs = {
    "genre": genres,
    "mood": moods,
    "target_energy": energy,
    "target_valence": valence,
    "target_danceability": dance,
    "target_tempo_bpm": tempo,
    "likes_acoustic": likes_acoustic,
}

results = recommend_songs(user_prefs, songs, k=5)

# ── Results ───────────────────────────────────────────────────────────────────
st.subheader("Your top picks")

for i, (song, score, explanation) in enumerate(results, 1):
    with st.container(border=True):
        left, right = st.columns([4, 1])
        with left:
            st.markdown(f"**{i}. {song['title']}** — {song['artist']}")
            st.caption(f"{song['genre'].title()} · {song['mood'].title()}")
            st.caption(explanation)
        with right:
            st.metric("Score", f"{score:.2f}")
