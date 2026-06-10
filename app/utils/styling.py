"""
styling.py

Centralized visual identity for the Credit Risk Decision Platform.
Premium dark-theme banking analytics aesthetic (Bloomberg / Palantir /
Aladdin-inspired): deep navy backgrounds, glass-effect cards, gradient
accents, and a consistent plotly_dark chart theme.
"""

import re

import plotly.io as pio
import streamlit as st


def _flatten_html(html: str) -> str:
    """
    Collapse a multi-line, indented HTML template literal into a single
    line with no leading whitespace.

    Streamlit's markdown renderer (CommonMark) treats any line indented
    by 4+ spaces as a fenced/indented code block, which causes raw HTML
    tags to be displayed as literal text instead of being parsed as HTML.
    All custom HTML components in this module are built as f-strings with
    Python-source indentation, so they must be flattened before being
    passed to st.markdown(..., unsafe_allow_html=True).
    """
    return re.sub(r"\n\s*", "", html).strip()


# Public alias for use by individual page modules.
flatten_html = _flatten_html

# ---------------------------------------------------------------------------
# Core Theme Colors
# ---------------------------------------------------------------------------
BG_PRIMARY = "#0B1220"
BG_SECONDARY = "#111827"
BG_CARD = "#1E293B"
BG_CARD_HOVER = "#334155"
BORDER_COLOR = "#334155"

TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#CBD5E1"
TEXT_MUTED = "#94A3B8"
TEXT_LABEL = "#CBD5E1"

ACCENT = "#3B82F6"
ACCENT_GRADIENT = "linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)"

SIDEBAR_BG = "#0B1220"
SIDEBAR_TEXT = "#F8FAFC"
SIDEBAR_SELECTED = "#3B82F6"

BG_MAIN = BG_PRIMARY  # backwards-compat alias

# ---------------------------------------------------------------------------
# Risk Colors (locked palette)
# ---------------------------------------------------------------------------
COLOR_LOW = "#22C55E"       # green
COLOR_MEDIUM = "#FACC15"    # yellow
COLOR_HIGH = "#F97316"      # orange
COLOR_CRITICAL = "#EF4444"  # red

SEGMENT_COLORS = {
    "Low Risk": COLOR_LOW,
    "Medium Risk": COLOR_MEDIUM,
    "High Risk": COLOR_HIGH,
    "Critical Risk": COLOR_CRITICAL,
}

SEGMENT_ACTIONS = {
    "Low Risk": "Auto Approve",
    "Medium Risk": "Standard Approval",
    "High Risk": "Manual Review",
    "Critical Risk": "Decline / Reprice",
}

# Aliases retained for any older imports referencing the original names
COLOR_DEFAULT = COLOR_CRITICAL
COLOR_NONDEFAULT = ACCENT
COLOR_NEUTRAL = TEXT_MUTED
PALETTE_RISK = "Reds"
COLOR_PRIMARY = TEXT_PRIMARY
COLOR_ACCENT = ACCENT
COLOR_SUCCESS = COLOR_LOW
COLOR_WARNING = COLOR_MEDIUM
COLOR_DANGER = COLOR_CRITICAL


# ---------------------------------------------------------------------------
# Plotly default template -- dark, transparent, consistent fonts/margins
# ---------------------------------------------------------------------------
def _configure_plotly_theme() -> None:
    pio.templates.default = "plotly_dark"
    template = pio.templates["plotly_dark"]
    template.layout.font.color = TEXT_SECONDARY
    template.layout.font.family = "Inter, 'Segoe UI', sans-serif"
    template.layout.title.font.color = TEXT_PRIMARY
    template.layout.title.font.size = 18
    template.layout.paper_bgcolor = "rgba(0,0,0,0)"
    template.layout.plot_bgcolor = "rgba(0,0,0,0)"
    template.layout.xaxis.gridcolor = "rgba(148,163,184,0.15)"
    template.layout.yaxis.gridcolor = "rgba(148,163,184,0.15)"
    template.layout.xaxis.linecolor = BORDER_COLOR
    template.layout.yaxis.linecolor = BORDER_COLOR
    template.layout.xaxis.tickfont.color = TEXT_MUTED
    template.layout.yaxis.tickfont.color = TEXT_MUTED
    template.layout.legend.font.color = TEXT_SECONDARY
    template.layout.margin = dict(l=40, r=20, t=60, b=40)


def inject_global_css() -> None:
    """Inject custom CSS for a premium dark banking analytics theme."""
    _configure_plotly_theme()

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }}

        /* ===================== Main app background & text ===================== */
        .stApp {{
            background: radial-gradient(circle at 20% 0%, #14213d 0%, {BG_PRIMARY} 45%) fixed;
            color: {TEXT_PRIMARY};
        }}

        [data-testid="stAppViewContainer"] {{
            color: {TEXT_PRIMARY};
        }}
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] span,
        [data-testid="stAppViewContainer"] li,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] div {{
            color: {TEXT_SECONDARY};
        }}

        /* Add breathing room around the main block */
        .block-container {{
            padding-top: 2.5rem;
            padding-bottom: 4rem;
            max-width: 1300px;
        }}

        /* ===================== Headings ===================== */
        [data-testid="stAppViewContainer"] h1 {{
            color: {TEXT_PRIMARY} !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }}
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3 {{
            color: {TEXT_PRIMARY} !important;
            font-weight: 600 !important;
            margin-top: 1.6rem;
        }}
        [data-testid="stAppViewContainer"] h4,
        [data-testid="stAppViewContainer"] h5,
        [data-testid="stAppViewContainer"] h6 {{
            color: {TEXT_PRIMARY} !important;
            font-weight: 600 !important;
        }}

        /* Captions / subtitles */
        [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
        [data-testid="stAppViewContainer"] .stCaption,
        [data-testid="stAppViewContainer"] small {{
            color: {TEXT_MUTED} !important;
        }}

        /* ===================== Sidebar (premium glass) ===================== */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0B1220 0%, #111827 100%);
            border-right: 1px solid {BORDER_COLOR};
        }}
        section[data-testid="stSidebar"] * {{
            color: {SIDEBAR_TEXT} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        section[data-testid="stSidebar"] small {{
            color: {TEXT_MUTED} !important;
        }}

        /* Sidebar nav links */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
            border-radius: 8px;
            margin: 2px 8px;
            padding: 8px 12px !important;
            transition: all 0.2s ease-in-out;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {{
            background-color: rgba(59, 130, 246, 0.15) !important;
            transform: translateX(2px);
        }}
        /* Selected / active nav link in sidebar */
        section[data-testid="stSidebar"] a[aria-current="page"] {{
            background: {ACCENT_GRADIENT} !important;
            color: #FFFFFF !important;
            border-radius: 8px;
            box-shadow: 0 0 16px rgba(59, 130, 246, 0.45);
        }}
        section[data-testid="stSidebar"] a[aria-current="page"] span {{
            color: #FFFFFF !important;
            font-weight: 600;
        }}

        /* ===================== KPI Cards (st.metric fallback) ===================== */
        div[data-testid="stMetric"] {{
            background: linear-gradient(160deg, {BG_CARD} 0%, #16213a 100%);
            border: 1px solid {BORDER_COLOR};
            border-top: 3px solid {ACCENT};
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 4px 18px rgba(0,0,0,0.35);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }}
        div[data-testid="stMetric"]:hover {{
            transform: translateY(-3px);
            border-color: {ACCENT};
            box-shadow: 0 8px 28px rgba(59,130,246,0.25);
        }}
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] * {{
            color: {TEXT_MUTED} !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-size: 0.78em !important;
        }}
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] * {{
            color: {TEXT_PRIMARY} !important;
            font-weight: 800 !important;
        }}
        div[data-testid="stMetricDelta"] {{
            color: {TEXT_SECONDARY} !important;
        }}

        /* ===================== Forms / Inputs ===================== */
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] .stSelectbox label,
        [data-testid="stAppViewContainer"] .stSlider label,
        [data-testid="stAppViewContainer"] .stNumberInput label,
        [data-testid="stAppViewContainer"] .stCheckbox label p {{
            color: {TEXT_LABEL} !important;
            font-weight: 500 !important;
        }}

        [data-testid="stAppViewContainer"] input,
        [data-testid="stAppViewContainer"] textarea,
        [data-testid="stAppViewContainer"] select {{
            color: {TEXT_PRIMARY} !important;
            background-color: {BG_CARD} !important;
            border: 1px solid {BORDER_COLOR} !important;
        }}
        [data-testid="stAppViewContainer"] [data-baseweb="select"] * {{
            color: {TEXT_PRIMARY} !important;
        }}
        [data-testid="stAppViewContainer"] [data-baseweb="select"] > div {{
            background-color: {BG_CARD} !important;
            border: 1px solid {BORDER_COLOR} !important;
            border-radius: 8px !important;
        }}
        [data-testid="stAppViewContainer"] [data-baseweb="input"] {{
            background-color: {BG_CARD} !important;
            border: 1px solid {BORDER_COLOR} !important;
            border-radius: 8px !important;
        }}
        [data-testid="stAppViewContainer"] [data-testid="stTickBarMin"],
        [data-testid="stAppViewContainer"] [data-testid="stTickBarMax"],
        [data-testid="stAppViewContainer"] [data-testid="stThumbValue"] {{
            color: {TEXT_SECONDARY} !important;
        }}

        /* Slider track accent */
        [data-testid="stAppViewContainer"] [data-baseweb="slider"] div[role="slider"] {{
            background-color: {ACCENT} !important;
            box-shadow: 0 0 8px rgba(59,130,246,0.6);
        }}

        /* ===================== Form "cards" (st.form containers) ===================== */
        [data-testid="stForm"] {{
            background: rgba(30, 41, 59, 0.55);
            backdrop-filter: blur(10px);
            border: 1px solid {BORDER_COLOR};
            border-radius: 16px;
            padding: 1.6rem 1.8rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.30);
        }}

        /* ===================== Buttons ===================== */
        [data-testid="stAppViewContainer"] button {{
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_COLOR};
            background-color: {BG_CARD};
            border-radius: 8px;
            transition: all 0.18s ease-in-out;
        }}
        [data-testid="stAppViewContainer"] button:hover {{
            border-color: {ACCENT};
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(59,130,246,0.25);
        }}
        [data-testid="stAppViewContainer"] button[kind="primary"],
        [data-testid="stAppViewContainer"] button[kind="formSubmit"] {{
            background: {ACCENT_GRADIENT} !important;
            color: #FFFFFF !important;
            border: none;
            font-weight: 700;
            font-size: 1.05em;
            padding: 0.7rem 1.5rem;
            box-shadow: 0 4px 20px rgba(59,130,246,0.35);
        }}
        [data-testid="stAppViewContainer"] button[kind="primary"]:hover,
        [data-testid="stAppViewContainer"] button[kind="formSubmit"]:hover {{
            box-shadow: 0 6px 28px rgba(59,130,246,0.55);
            transform: translateY(-2px);
        }}
        [data-testid="stAppViewContainer"] button[kind="primary"] *,
        [data-testid="stAppViewContainer"] button[kind="formSubmit"] * {{
            color: #FFFFFF !important;
        }}

        /* ===================== Tabs ===================== */
        button[data-baseweb="tab"] {{
            font-weight: 600;
            color: {TEXT_MUTED} !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {ACCENT} !important;
        }}
        button[data-baseweb="tab"] * {{
            color: inherit !important;
        }}

        /* ===================== Tables / Dataframes ===================== */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {BORDER_COLOR};
            border-radius: 12px;
            overflow: hidden;
            background-color: {BG_CARD};
        }}

        /* ===================== Alert / info / success boxes ===================== */
        [data-testid="stAppViewContainer"] [data-testid="stAlertContainer"] {{
            color: {TEXT_PRIMARY} !important;
            background-color: rgba(30, 41, 59, 0.65);
            border: 1px solid {BORDER_COLOR};
            border-radius: 12px;
        }}
        [data-testid="stAppViewContainer"] [data-testid="stAlertContainer"] * {{
            color: {TEXT_PRIMARY} !important;
        }}

        /* ===================== Section dividers ===================== */
        hr {{
            border-top: 1px solid {BORDER_COLOR};
            margin: 1.8rem 0;
        }}

        /* ===================== Markdown links ===================== */
        [data-testid="stAppViewContainer"] a {{
            color: {ACCENT} !important;
        }}

        /* ===================== Animations ===================== */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        [data-testid="stAppViewContainer"] .block-container > div {{
            animation: fadeInUp 0.45s ease-out;
        }}

        /* ===================== Custom component classes ===================== */
        .hero-banner {{
            background: linear-gradient(120deg, #1e3a8a 0%, #312e81 50%, #0B1220 100%);
            border: 1px solid {BORDER_COLOR};
            border-radius: 20px;
            padding: 2.6rem 2.8rem;
            margin-bottom: 1.8rem;
            box-shadow: 0 12px 40px rgba(0,0,0,0.45);
            animation: fadeInUp 0.5s ease-out;
        }}
        .hero-title {{
            font-size: 2.4rem;
            font-weight: 800;
            line-height: 1.2;
            color: {TEXT_PRIMARY};
            margin: 0 0 0.6rem 0;
            letter-spacing: -0.5px;
        }}
        .hero-subtitle {{
            font-size: 1.1rem;
            color: {TEXT_SECONDARY};
            font-weight: 400;
            margin: 0;
        }}

        .flow-panel {{
            background: rgba(30, 41, 59, 0.55);
            backdrop-filter: blur(12px);
            border: 1px solid {BORDER_COLOR};
            border-radius: 18px;
            padding: 1.8rem;
            margin: 1.4rem 0;
            box-shadow: 0 8px 30px rgba(0,0,0,0.30);
        }}
        .flow-step {{
            background: linear-gradient(160deg, {BG_CARD} 0%, #16213a 100%);
            border: 1px solid {BORDER_COLOR};
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            text-align: center;
            transition: all 0.2s ease;
            height: 100%;
        }}
        .flow-step:hover {{
            border-color: {ACCENT};
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(59,130,246,0.25);
        }}
        .flow-step .flow-label {{
            color: {TEXT_MUTED};
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 600;
            margin-bottom: 6px;
        }}
        .flow-step .flow-value {{
            color: {TEXT_PRIMARY};
            font-size: 1.05rem;
            font-weight: 700;
        }}
        .flow-arrow-row {{
            text-align: center;
            color: {ACCENT};
            font-size: 1.4rem;
            font-weight: 700;
            line-height: 1;
        }}

        /* KPI grid cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 1.1rem;
            margin: 1.2rem 0;
        }}
        .kpi-card {{
            background: linear-gradient(160deg, {BG_CARD} 0%, #16213a 100%);
            border: 1px solid {BORDER_COLOR};
            border-radius: 14px;
            padding: 1.3rem 1.4rem;
            border-top: 3px solid var(--kpi-accent, {ACCENT});
            box-shadow: 0 4px 18px rgba(0,0,0,0.35);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
            animation: fadeInUp 0.5s ease-out;
        }}
        .kpi-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 30px rgba(59,130,246,0.30), 0 0 0 1px var(--kpi-accent, {ACCENT}) inset;
        }}
        .kpi-card .kpi-label {{
            color: {TEXT_MUTED};
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 8px;
        }}
        .kpi-card .kpi-value {{
            color: {TEXT_PRIMARY};
            font-size: 1.9rem;
            font-weight: 800;
            line-height: 1.1;
        }}
        .kpi-card .kpi-sub {{
            color: {TEXT_SECONDARY};
            font-size: 0.82rem;
            margin-top: 6px;
        }}

        /* Section header with gradient underline */
        .section-header {{
            font-size: 1.35rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            margin: 1.8rem 0 0.4rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid transparent;
            border-image: {ACCENT_GRADIENT};
            border-image-slice: 1;
            display: inline-block;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_branding() -> None:
    """Render premium glass-style branding block at the top of the sidebar."""
    st.sidebar.markdown(
        _flatten_html(f"""
        <div style="padding: 12px 4px 16px 4px;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                <div style="width:38px; height:38px; border-radius:10px;
                            background:{ACCENT_GRADIENT}; display:flex;
                            align-items:center; justify-content:center;
                            font-size:1.3rem; box-shadow:0 0 16px rgba(59,130,246,0.5);">
                    &#128202;
                </div>
                <div>
                    <div style="font-size:1.05rem; font-weight:800; color:{TEXT_PRIMARY}; line-height:1.1;">
                        Credit Risk
                    </div>
                    <div style="font-size:0.95rem; font-weight:700; background:{ACCENT_GRADIENT};
                                -webkit-background-clip:text; background-clip:text; color:transparent; line-height:1.1;">
                        Decision Platform
                    </div>
                </div>
            </div>
            <p style="font-size:0.78em; color:{TEXT_MUTED}; margin:0;">
                Early Warning &amp; Risk-Based Loan Pricing Engine<br/>
                LendingClub 2007&ndash;2018
            </p>
        </div>
        <hr style="border-top: 1px solid {BORDER_COLOR}; margin: 0.4rem 0 0.8rem 0;"/>
        """),
        unsafe_allow_html=True,
    )


def render_sidebar_footer() -> None:
    """Render a fixed-style footer at the bottom of the sidebar."""
    st.sidebar.markdown(
        _flatten_html(f"""
        <div style="margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid {BORDER_COLOR};">
            <p style="font-size:0.75em; color:{TEXT_MUTED}; margin:0;">Built by</p>
            <p style="font-size:0.95em; font-weight:700; color:{TEXT_PRIMARY}; margin:0;">Priyanshi</p>
            <p style="font-size:0.72em; color:{TEXT_MUTED}; margin-top:2px;">
                Credit Risk Analytics Portfolio Project
            </p>
        </div>
        """),
        unsafe_allow_html=True,
    )


def kpi_card_row(items: list[tuple[str, str, str | None]]) -> None:
    """
    Render a row of premium KPI cards (replaces st.metric with custom
    glassmorphism cards: large value, small label, colored top border,
    hover glow).

    Parameters
    ----------
    items : list of (label, value, delta) tuples. delta may be None.
    """
    accents = [ACCENT, COLOR_LOW, COLOR_MEDIUM, COLOR_HIGH, COLOR_CRITICAL, "#8B5CF6"]

    cards_html = '<div class="kpi-grid">'
    for i, (label, value, delta) in enumerate(items):
        accent = accents[i % len(accents)]
        sub_html = f'<div class="kpi-sub">{delta}</div>' if delta else ""
        cards_html += _flatten_html(f"""
        <div class="kpi-card" style="--kpi-accent:{accent};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {sub_html}
        </div>
        """)
    cards_html += "</div>"

    st.markdown(cards_html, unsafe_allow_html=True)


def render_hero(title_lines: list[str], subtitle: str) -> None:
    """Render the large gradient hero banner used on the landing page."""
    title_html = "<br/>".join(title_lines)
    st.markdown(
        _flatten_html(f"""
        <div class="hero-banner">
            <div class="hero-title">{title_html}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_flow_panel(steps: list[tuple[str, str]]) -> None:
    """
    Render the executive workflow panel as a horizontal sequence of
    glass cards connected by accent-colored arrows.

    Parameters
    ----------
    steps : list of (label, value) tuples, e.g. ("Problem", "Predict Default Risk")
    """
    cols_html = ""
    for i, (label, value) in enumerate(steps):
        cols_html += _flatten_html(f"""
        <div style="flex:1; min-width:160px;">
            <div class="flow-step">
                <div class="flow-label">{label}</div>
                <div class="flow-value">{value}</div>
            </div>
        </div>
        """)
        if i < len(steps) - 1:
            cols_html += '<div class="flow-arrow-row" style="display:flex; align-items:center;">&#8594;</div>'

    st.markdown(
        _flatten_html(f"""
        <div class="flow-panel">
            <div style="display:flex; align-items:stretch; gap:0.8rem; flex-wrap:wrap;">
                {cols_html}
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def section_header(title: str) -> None:
    """Render a section header with a gradient underline accent."""
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def segment_badge_html(segment: str) -> str:
    """Return a high-contrast HTML badge for a risk segment (white text on colored background)."""
    color = SEGMENT_COLORS.get(segment, TEXT_MUTED)
    action = SEGMENT_ACTIONS.get(segment, "Review")
    return _flatten_html(f"""
    <div style="display:inline-block; padding:12px 22px; border-radius:10px;
                background:{color}; color:#FFFFFF; font-weight:700;
                font-size:1.15em; text-align:center;
                box-shadow: 0 6px 20px {color}55;">
        <span style="color:#FFFFFF;">{segment}</span>
        <div style="font-size:0.72em; font-weight:600; margin-top:4px; color:#FFFFFF; opacity:0.95;">
            Recommended Action: {action}
        </div>
    </div>
    """)
