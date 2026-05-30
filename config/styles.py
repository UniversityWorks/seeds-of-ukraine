"""
config/styles.py
================
Central CSS stylesheet for the Seeds of Ukraine platform.

Keeping CSS in its own module means:
  • A designer can edit styles without touching any Python logic.
  • The stylesheet is injected once by the shell component and is available
    globally for the session — no per-page duplication.
  • Variables mirror the Python colour constants in config/settings.py so
    Plotly charts and CSS stay visually in sync.
"""

GLOBAL_CSS = """
<style>
/* ═══════════════════════════════════════════════════════════════════════════
   GOOGLE FONTS
   ═══════════════════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ═══════════════════════════════════════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════════════════════════════════════ */
:root {
    --green-deep:   #1a3c2b;
    --green-mid:    #2d6a4f;
    --green-light:  #52b788;
    --green-pale:   #d8f3dc;
    --gold:         #d4a017;
    --gold-light:   #f5e6aa;
    --earth:        #6b4226;
    --cream:        #faf7f0;
    --white:        #ffffff;
    --text-dark:    #1a2810;
    --text-mid:     #3d5a40;
    --text-muted:   #7a9e7e;
    --border:       #c8e6c9;
    --shadow:       0 4px 24px rgba(26,60,43,0.10);
    --radius:       12px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   GLOBAL RESET
   ═══════════════════════════════════════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--cream);
    color: var(--text-dark);
}

/* ═══════════════════════════════════════════════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--green-deep) 0%, var(--green-mid) 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color: var(--cream) !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput  label,
[data-testid="stSidebar"] .stNumberInput label {
    color: var(--gold-light) !important;
    font-weight: 500;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }
[data-testid="stSidebarNav"] { display: none; }

/* ═══════════════════════════════════════════════════════════════════════════
   HEADER BANNER
   ═══════════════════════════════════════════════════════════════════════════ */
.sou-header {
    background: linear-gradient(135deg, var(--green-deep) 0%, var(--green-mid) 60%, var(--green-light) 100%);
    border-radius: var(--radius);
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    box-shadow: var(--shadow);
}
.sou-header-icon  { font-size: 3.5rem; line-height: 1; }
.sou-header-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: var(--white);
    margin: 0;
    letter-spacing: -0.01em;
}
.sou-header-sub {
    font-size: 1rem;
    color: var(--green-pale);
    margin: 0.25rem 0 0;
    font-weight: 300;
}
.sou-badge {
    background: var(--gold);
    color: var(--green-deep);
    font-size: 0.65rem;
    font-weight: 700;
    padding: 0.2em 0.75em;
    border-radius: 20px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-left: 0.75rem;
    vertical-align: middle;
}

/* ═══════════════════════════════════════════════════════════════════════════
   METRIC CARDS
   ═══════════════════════════════════════════════════════════════════════════ */
.metric-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.metric-card {
    flex: 1;
    background: var(--white);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    border-left: 4px solid var(--green-light);
    box-shadow: var(--shadow);
    transition: transform 0.2s;
}
.metric-card:hover { transform: translateY(-2px); }
.metric-card.gold  { border-left-color: var(--gold); }
.metric-card.earth { border-left-color: var(--earth); }
.metric-card.dark  { border-left-color: var(--green-deep); }
.mc-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--text-muted);
    margin-bottom: 0.4rem;
}
.mc-value {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--green-deep);
    line-height: 1;
}
.mc-delta { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.3rem; }

/* ═══════════════════════════════════════════════════════════════════════════
   TYPOGRAPHY HELPERS
   ═══════════════════════════════════════════════════════════════════════════ */
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: var(--green-deep);
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--green-pale);
    font-weight: 700;
}
.section-sub {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 1rem;
}

/* ═══════════════════════════════════════════════════════════════════════════
   DATA TABLES
   ═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] { border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); }
.stDataFrame thead th {
    background: var(--green-deep) !important;
    color: var(--cream) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
.stDataFrame tbody tr:hover { background: var(--green-pale) !important; }

/* ═══════════════════════════════════════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════════════════════════════════════ */
.stButton > button {
    background: linear-gradient(135deg, var(--green-mid), var(--green-deep));
    color: var(--white) !important;
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1.5rem;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 0.875rem;
    letter-spacing: 0.02em;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 2px 8px rgba(26,60,43,0.25);
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(26,60,43,0.35); }
.stButton > button[kind="secondary"] {
    background: var(--cream);
    color: var(--green-deep) !important;
    border: 1px solid var(--border);
}

/* ═══════════════════════════════════════════════════════════════════════════
   FORM INPUTS
   ═══════════════════════════════════════════════════════════════════════════ */
.stTextInput   > div > div,
.stNumberInput > div > div,
.stSelectbox   > div > div,
.stDateInput   > div > div,
.stTextArea    > div {
    border-radius: 8px !important;
    border-color: var(--border) !important;
    background: var(--white) !important;
}
.stTextInput   > label, .stNumberInput > label,
.stSelectbox   > label, .stDateInput   > label,
.stTextArea    > label {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: var(--text-mid) !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   TABS
   ═══════════════════════════════════════════════════════════════════════════ */
.stTabs [role="tablist"] {
    background: var(--white);
    border-radius: var(--radius);
    padding: 0.35rem;
    gap: 0.25rem;
    box-shadow: 0 2px 8px rgba(26,60,43,0.07);
}
.stTabs [role="tab"] {
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    color: var(--text-muted);
    padding: 0.5rem 1rem;
    transition: all 0.2s;
}
.stTabs [role="tab"][aria-selected="true"] {
    background: var(--green-mid);
    color: var(--white) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   CALLOUT CARDS
   ═══════════════════════════════════════════════════════════════════════════ */
.info-card {
    background: var(--green-pale);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    border: 1px solid var(--border);
    margin-bottom: 1rem;
    font-size: 0.875rem;
    color: var(--green-deep);
}
.filter-panel {
    background: var(--white);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    border: 1px solid var(--border);
    box-shadow: 0 2px 8px rgba(26,60,43,0.06);
}

/* ═══════════════════════════════════════════════════════════════════════════
   REMINDER PILLS  (Care Planner tab)
   ═══════════════════════════════════════════════════════════════════════════ */
.reminder-pill {
    display: inline-block;
    background: var(--gold-light);
    color: var(--earth);
    border-radius: 20px;
    padding: 0.25em 0.9em;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0.2em;
    border: 1px solid var(--gold);
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCROLLBAR
   ═══════════════════════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--cream); }
::-webkit-scrollbar-thumb { background: var(--green-light); border-radius: 3px; }
</style>
"""
