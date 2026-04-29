AURA_CSS = """
<style>
/* ── Page background ── */
[data-testid="stAppViewContainer"] {
    background: #0f0d1a;
}
[data-testid="stHeader"] {
    background: #0f0d1a;
}
[data-testid="stSidebar"] {
    background: #12101f;
}

/* ── Gradient blobs (decorative) ── */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: -80px;
    right: -60px;
    width: 380px;
    height: 380px;
    border-radius: 50%;
    background: radial-gradient(circle, #3d2f7a 0%, #1e1638 50%, transparent 72%);
    opacity: 0.5;
    pointer-events: none;
    z-index: 0;
}
[data-testid="stAppViewContainer"]::after {
    content: "";
    position: fixed;
    bottom: 60px;
    left: -80px;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, #2a1a5e 0%, #150f2a 50%, transparent 72%);
    opacity: 0.55;
    pointer-events: none;
    z-index: 0;
}

/* ── Main content block ── */
[data-testid="stMainBlockContainer"] {
    position: relative;
    z-index: 1;
}
.block-container {
    padding-top: 2.5rem !important;
    max-width: 780px;
}

/* ── Hero block ── */
.aura-hero {
    position: relative;
    overflow: hidden;
    padding: 1.7rem;
    margin-bottom: 1.4rem;
    background: linear-gradient(145deg, rgba(24, 19, 52, 0.96), rgba(18, 15, 35, 0.92));
    border: 1px solid #2a2240;
    border-radius: 18px;
    box-shadow: 0 18px 44px rgba(6, 4, 18, 0.35);
}
.aura-hero::before {
    content: "";
    position: absolute;
    inset: -20% auto auto 64%;
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(157, 128, 255, 0.3) 0%, rgba(92, 63, 204, 0.08) 55%, transparent 72%);
    pointer-events: none;
}
.aura-kicker {
    margin-bottom: 0.65rem;
    color: #9d90c4;
    font-family: monospace;
    font-size: 0.75rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}
.aura-hero p {
    max-width: 36rem;
    margin-bottom: 0 !important;
}
.aura-chip-row {
    display: flex;
    gap: 0.55rem;
    flex-wrap: wrap;
    margin-top: 1rem;
}
.aura-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.7rem;
    background: rgba(61, 47, 122, 0.45);
    border: 1px solid rgba(157, 128, 255, 0.45);
    border-radius: 999px;
    color: #d7ccff;
    font-family: monospace;
    font-size: 0.74rem;
    letter-spacing: 0.03em;
}
.aura-section-label {
    margin-bottom: 0.5rem;
    color: #8d81b3;
    font-family: monospace;
    font-size: 0.74rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

/* ── Typography ── */
h1, h2, h3, h4, h5, h6 {
    color: #f0ecff !important;
    font-family: 'Georgia', serif !important;
    letter-spacing: -0.3px;
}
h1 { font-size: 2rem !important; }
p, span, label, div {
    color: #c8bfe8;
}
.stCaption, [data-testid="stCaptionContainer"] {
    color: #7a6fa0 !important;
    font-family: monospace !important;
    font-size: 0.75rem !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #2a2240;
    gap: 0;
}
[data-testid="stTabs"] [role="tab"] {
    color: #7a6fa0 !important;
    font-family: monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.04em;
    background: transparent !important;
    border: none !important;
    padding: 10px 18px !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #c4b5fd !important;
    border-bottom: 2px solid #7c5ff5 !important;
}
[data-testid="stTabs"] [role="tab"]:hover {
    color: #a898d8 !important;
}

/* ── Buttons ── */
.stButton > button,
.stFormSubmitButton > button,
.stLinkButton > a {
    background: linear-gradient(135deg, #6b4de0, #4a2fa8) !important;
    color: #f0ecff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.55rem 1.4rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover,
.stLinkButton > a:hover {
    background: linear-gradient(135deg, #7c5ff5, #5c3fcc) !important;
    border: none !important;
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    width: 100%;
}

/* ── Text inputs & text areas ── */
.stTextArea textarea,
.stTextInput input {
    background: #1a1630 !important;
    border: 1px solid #2a2240 !important;
    border-radius: 10px !important;
    color: #c8bfe8 !important;
    font-family: monospace !important;
    font-size: 0.85rem !important;
}
.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
    color: #3d3460 !important;
}
.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: #5c3fcc !important;
    box-shadow: 0 0 0 2px #3d2f7a55 !important;
}

/* ── Multiselect ── */
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
    background: #1a1630 !important;
    border: 1px solid #2a2240 !important;
    border-radius: 8px !important;
    color: #c8bfe8 !important;
}
[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background: linear-gradient(135deg, #3d2f7a, #2a1f5e) !important;
    border: 1px solid #7c5ff5 !important;
    border-radius: 20px !important;
    color: #d4c8ff !important;
    font-family: monospace !important;
    font-size: 0.72rem !important;
}
[data-testid="stMultiSelect"] [data-baseweb="select"] input {
    color: #c8bfe8 !important;
}

/* ── Selectbox dropdown ── */
[data-baseweb="popover"] {
    background: #1a1630 !important;
    border: 1px solid #2a2240 !important;
}
[data-baseweb="menu"] li {
    background: #1a1630 !important;
    color: #c8bfe8 !important;
    font-family: monospace !important;
    font-size: 0.82rem !important;
}
[data-baseweb="menu"] li:hover {
    background: #2a2048 !important;
}

/* ── Sliders ── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: linear-gradient(135deg, #7c5ff5, #5c3fcc) !important;
    border: 2px solid #c4b5fd !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[class*="Track"] {
    background: #2a2240 !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[class*="Track"]:first-child {
    background: linear-gradient(90deg, #5c3fcc, #9d80ff) !important;
}
[data-testid="stSlider"] label {
    color: #9d90c4 !important;
    font-family: monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
[data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-testid="stTickBarMax"] {
    color: #4a3f6a !important;
    font-family: monospace !important;
}

/* ── Toggle ── */
[data-testid="stToggle"] label {
    color: #9d90c4 !important;
    font-family: monospace !important;
}
[data-testid="stToggle"] input:checked + div {
    background: linear-gradient(135deg, #6b4de0, #4a2fa8) !important;
}

/* ── Containers / cards ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: linear-gradient(135deg, #16122a, #1a1438) !important;
    border: 1px solid #2a2240 !important;
    border-radius: 12px !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover > div {
    border-color: #3d2f7a !important;
}

/* ── Metric (score) ── */
[data-testid="stMetric"] {
    text-align: center;
}
[data-testid="stMetricLabel"] {
    color: #5a4f78 !important;
    font-family: monospace !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}
[data-testid="stMetricValue"] {
    color: #c4b5fd !important;
    font-family: monospace !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}

/* ── Divider ── */
hr {
    border-color: #2a2240 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] details {
    background: #16122a !important;
    border: 1px solid #2a2240 !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    color: #9d90c4 !important;
    font-family: monospace !important;
    font-size: 0.8rem !important;
}

/* ── Code block (playlist) ── */
[data-testid="stCode"] {
    background: linear-gradient(135deg, #16122a, #1c1540) !important;
    border: 1px solid #2a2240 !important;
    border-radius: 8px !important;
}
[data-testid="stCode"] pre {
    background: transparent !important;
    color: #9d90c4 !important;
    font-size: 0.82rem !important;
    line-height: 1.9 !important;
}

/* ── Info / warning / error alerts ── */
[data-testid="stAlert"] {
    background: #1e1638 !important;
    border: 1px solid #3a3060 !important;
    border-radius: 8px !important;
    color: #c8bfe8 !important;
    font-family: monospace !important;
    font-size: 0.8rem !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] {
    color: #c4b5fd !important;
}

/* ── Subheader accent bar ── */
h2::before {
    content: "// ";
    color: #5c3fcc;
    font-family: monospace;
    font-size: 0.9em;
}

/* ── Gradient accent bar under title ── */
h1::after {
    content: "";
    display: block;
    height: 2px;
    width: 100%;
    background: linear-gradient(90deg, transparent, #5c3fcc, #9d80ff, #c4b5fd, transparent);
    border-radius: 2px;
    margin-top: 12px;
    opacity: 0.7;
}

/* ── Markdown text ── */
[data-testid="stMarkdownContainer"] p {
    color: #c8bfe8 !important;
    font-size: 0.9rem;
}
[data-testid="stMarkdownContainer"] strong {
    color: #e8e0ff !important;
}
</style>
"""
