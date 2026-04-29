import os
import urllib.parse
from typing import get_args

import streamlit as st
from dotenv import load_dotenv

from src.recommender import load_songs, recommend_songs
from src.retrieval import VignetteRetriever
from src.extractor import VibeExtractor
from src.schema import GENRES, MOODS
from aura_theme import AURA_CSS

load_dotenv()

st.set_page_config(page_title="Aura", page_icon="🎧", layout="centered")

# ── Inject theme ──────────────────────────────────────────────────────────────
st.markdown(AURA_CSS, unsafe_allow_html=True)

GENRE_OPTIONS = list(get_args(GENRES))
MOOD_OPTIONS = list(get_args(MOODS))


@st.cache_data
def get_songs():
    return load_songs("data/songs.csv")


@st.cache_resource
def get_retriever() -> VignetteRetriever:
    return VignetteRetriever("data/vignettes.jsonl")


@st.cache_resource
def get_extractor() -> VibeExtractor:
    return VibeExtractor(get_retriever())


def spotify_search_url(title: str, artist: str) -> str:
    query = urllib.parse.quote_plus(f"{title} {artist}")
    return f"https://open.spotify.com/search/{query}"


songs = get_songs()

st.title("🎧 Aura")
st.caption("Tell it what you're feeling. Get five songs back.")

if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    st.error(
        "Missing `GEMINI_API_KEY`. Copy `.env.example` to `.env` and add your key "
        "(free at https://aistudio.google.com/app/apikey). "
        "The vibe check-in will fall back to a safe preset until then."
    )

st.divider()

st.session_state.setdefault("current_prefs", None)
st.session_state.setdefault("extraction_meta", None)

tab_vibe, tab_manual = st.tabs(["✨ Vibe check-in", "🎚 Manual tuning"])

# ── Tab 1: Vibe check-in ─────────────────────────────────────────────────────
with tab_vibe:
    st.write("Tell me what's going on. I'll pick the music.")

    with st.form("vibe_form"):
        bubbles = st.multiselect(
            "Pick a few moods (optional)",
            options=MOOD_OPTIONS,
            default=[],
        )
        free_text = st.text_area(
            "Or describe the vibe in your own words",
            placeholder="I just passed Calc II. Or: rainy day, can't focus...",
            height=100,
        )
        submitted = st.form_submit_button("Get my picks", type="primary")

    if submitted:
        if not bubbles and not free_text.strip():
            st.warning("Pick at least one mood or write something.")
        else:
            with st.spinner("Reading your vibe..."):
                prefs, meta = get_extractor().extract(free_text, bubbles)
            st.session_state.current_prefs = prefs.to_recommender_dict()
            st.session_state.extraction_meta = meta
            if meta["fallback_used"]:
                st.warning(
                    f"Couldn't read your vibe ({meta['error'] or 'unknown error'}). "
                    "Used your mood selections instead."
                )

    if st.session_state.extraction_meta:
        meta = st.session_state.extraction_meta
        with st.expander("Why these settings?"):
            st.markdown("**Retrieved vignettes (closest matches in the corpus):**")
            for text, score in zip(meta["retrieved"], meta["retrieved_scores"]):
                st.markdown(f"- *({score:.2f})* {text}")
            if st.session_state.current_prefs:
                st.markdown("**Extracted preferences:**")
                st.json(st.session_state.current_prefs)
            st.caption(
                f"Latency: {meta['latency_ms']} ms · "
                f"Schema valid: {meta['schema_valid']} · "
                f"Fallback used: {meta['fallback_used']}"
            )

# ── Tab 2: Manual tuning ─────────────────────────────────────────────────────
with tab_manual:
    col1, col2 = st.columns(2)
    with col1:
        m_genres = st.multiselect(
            "Genres", GENRE_OPTIONS, default=["pop"], key="m_genres"
        )
        m_moods = st.multiselect(
            "Moods", MOOD_OPTIONS, default=["happy"], key="m_moods"
        )
        m_likes_acoustic = st.toggle(
            "I like acoustic music", value=False, key="m_acoustic"
        )
    with col2:
        m_energy = st.slider("Energy", 0.0, 1.0, 0.7, 0.05, key="m_energy")
        m_valence = st.slider("Positivity", 0.0, 1.0, 0.7, 0.05, key="m_valence")
        m_dance = st.slider("Danceability", 0.0, 1.0, 0.7, 0.05, key="m_dance")
        m_tempo = st.slider("Tempo (BPM)", 60, 200, 120, 5, key="m_tempo")

    if st.button("Apply manual tuning", type="primary"):
        if not m_genres or not m_moods:
            st.warning("Pick at least one genre and one mood.")
        else:
            st.session_state.current_prefs = {
                "genre": m_genres,
                "mood": m_moods,
                "target_energy": m_energy,
                "target_valence": m_valence,
                "target_danceability": m_dance,
                "target_tempo_bpm": m_tempo,
                "likes_acoustic": m_likes_acoustic,
            }
            st.session_state.extraction_meta = None

# ── Results ──────────────────────────────────────────────────────────────────
st.divider()

if not st.session_state.current_prefs:
    st.info("Submit a vibe or manual tuning above to see picks.")
    st.stop()

results = recommend_songs(st.session_state.current_prefs, songs, k=5)

st.subheader("Your top picks")

for i, (song, score, explanation) in enumerate(results, 1):
    with st.container(border=True):
        left, right = st.columns([4, 1])
        with left:
            st.markdown(f"**{i}. {song['title']}** — {song['artist']}")
            st.caption(f"{song['genre'].title()} · {song['mood'].title()}")
            st.caption(explanation)
            st.link_button(
                "Open in Spotify ↗",
                spotify_search_url(song["title"], song["artist"]),
                use_container_width=True,
            )
        with right:
            st.metric("Score", f"{score:.2f}")

# ── Copy-paste playlist ─────────────────────────────────────────────────────
st.divider()
st.subheader("📋 Build playlist on Spotify")
st.caption("Copy this list, paste each line into Spotify (Prompted Playlist), save what you like.")
playlist_text = "\n".join(
    f"{song['title']} - {song['artist']}" for song, _, _ in results
)
st.code(playlist_text, language="text")