from pathlib import Path

import streamlit as st


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

        :root {
            --app-bg: #f6f7fb;
            --surface: #ffffff;
            --surface-soft: #f8f9ff;
            --border: #e2e7f0;
            --text-main: #182033;
            --text-muted: #697386;
            --accent: #5b5bf0;
            --accent-dark: #4747d7;
            --accent-soft: #eeeeff;
            --accent-gradient: linear-gradient(135deg, #6366f1, #8b5cf6);
            --success: #15803d;
            --success-soft: #eaf8ef;
            --warning: #a16207;
            --warning-soft: #fff8df;
            --danger: #dc2626;
            --danger-soft: #fff0f0;
            --shadow-sm: 0 1px 2px rgba(24, 32, 51, 0.04), 0 4px 14px rgba(24, 32, 51, 0.04);
            --shadow-md: 0 12px 30px rgba(76, 78, 160, 0.10);
        }
        html, body, [class*="css"], .stApp {
            font-family: "Inter", sans-serif;
        }
        .stApp { background: var(--app-bg); color: var(--text-main); }
        [data-testid="stSidebarNav"] { display: none; }
        [data-testid="stAppViewContainer"] .main .block-container,
        [data-testid="stMainBlockContainer"],
        .main .block-container {
            width: 100%;
            max-width: none;
            padding-top: 1.75rem;
            padding-bottom: 3rem;
            padding-left: clamp(0.75rem, 1.2vw, 1.5rem);
            padding-right: clamp(0.75rem, 1.2vw, 1.5rem);
        }
        [data-testid="stAppViewContainer"] {
            padding-left: 0;
            padding-right: 0;
        }
        [data-testid="stAppViewContainer"] .main {
            max-width: none;
            width: 100%;
        }
        .main .block-container,
        .main .block-container p,
        .main .block-container span,
        .main .block-container label,
        .main .block-container div[data-testid="stMarkdownContainer"],
        .stApp label,
        .stApp p,
        .stApp span,
        .stApp div[data-testid="stWidgetLabel"],
        .stApp div[data-testid="stCaptionContainer"],
        .stApp div[data-testid="stMarkdownContainer"] {
            color: var(--text-main) !important;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: "Plus Jakarta Sans", sans-serif;
            color: var(--text-main);
            letter-spacing: 0;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            background: #ffffff;
            border-color: #cbd5e1;
            color: var(--text-main);
        }
        div[data-baseweb="select"] *,
        div[data-baseweb="input"] *,
        div[data-baseweb="textarea"] *,
        div[data-testid="stNumberInput"] *,
        div[data-testid="stTextInput"] *,
        div[data-testid="stSelectbox"] *,
        div[data-testid="stRadio"] *,
        div[data-testid="stCheckbox"] *,
        div[data-testid="stExpander"] * {
            color: var(--text-main) !important;
        }
        div[data-testid="stExpander"] {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: var(--shadow-sm);
            overflow: hidden;
        }
        button[role="tab"] *,
        div[data-testid="stTabs"] * {
            color: var(--text-main);
        }
        section[data-testid="stSidebar"] {
            background: #f2f3fb;
            border-right: 1px solid var(--border);
            color: var(--text-main);
        }
        section[data-testid="stSidebar"] * {
            color: var(--text-main) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {
            color: #475569 !important;
        }
        section[data-testid="stSidebar"] code {
            background: #dbeafe;
            color: #1e3a8a !important;
            border: 1px solid #bfdbfe;
        }
        .sidebar-brand {
            position: relative;
            overflow: hidden;
            background: var(--accent-gradient);
            border: 0;
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0 12px 26px rgba(91, 91, 240, 0.20);
        }
        .sidebar-brand-title {
            font-weight: 800;
            font-size: 1rem;
            margin-bottom: 4px;
            color: #ffffff !important;
        }
        .sidebar-brand-subtitle {
            color: rgba(255, 255, 255, 0.82) !important;
            font-size: 0.82rem;
            line-height: 1.35;
        }
        .nav-label {
            margin: 4px 0 8px 0;
            color: #64748b !important;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .nav-active {
            display: block;
            background: #ffffff;
            border: 1px solid #d9dcff;
            border-left: 4px solid var(--accent);
            border-radius: 12px;
            padding: 12px 13px;
            margin: 6px 0;
            color: var(--text-main);
            font-weight: 800;
            box-shadow: 0 6px 18px rgba(91, 91, 240, 0.10);
        }
        .nav-link {
            display: block;
            background: transparent;
            border: 1px solid transparent;
            border-radius: 12px;
            padding: 12px 13px;
            margin: 6px 0;
            color: var(--text-main) !important;
            font-weight: 750;
            text-decoration: none !important;
        }
        .nav-link:hover {
            background: #ffffff;
            border-color: #dfe1ff;
            transform: translateY(-1px);
            box-shadow: var(--shadow-sm);
            text-decoration: none !important;
        }
        .nav-link-title {
            display: block;
            color: var(--text-main) !important;
            font-weight: 800;
        }
        .nav-hint {
            display: block;
            color: var(--text-muted) !important;
            font-size: 0.78rem;
            margin-top: 4px;
            font-weight: 500;
        }
        div[data-testid="stAlert"] {
            border-radius: 14px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-sm);
        }
        div[data-testid="stAlert"] * {
            color: var(--text-main) !important;
        }
        div[data-testid="stFileUploader"] section {
            background: #ffffff;
            border: 1.5px dashed #b7b9ec;
            border-radius: 16px;
            padding: 0.5rem;
            transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
        }
        div[data-testid="stFileUploader"] section:hover {
            border-color: var(--accent);
            box-shadow: 0 10px 25px rgba(91, 91, 240, 0.09);
            transform: translateY(-1px);
        }
        div[data-testid="stFileUploader"] section * {
            color: var(--text-main) !important;
        }
        div[data-testid="stFileUploader"] button {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1d4ed8 !important;
        }
        div[data-testid="stFileUploader"] small {
            color: var(--text-muted) !important;
        }
        div[data-testid="stMetric"] {
            position: relative;
            overflow: hidden;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: var(--shadow-sm);
            transition: transform 160ms ease, box-shadow 160ms ease;
        }
        div[data-testid="stMetric"]::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: var(--accent-gradient);
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        div[data-testid="stMetricLabel"] p { color: var(--text-muted); font-size: 0.86rem; }
        div[data-testid="stMetricValue"] { color: var(--text-main); font-weight: 700; }
        .app-hero {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, #ffffff 0%, #f0f1ff 52%, #f5edff 100%);
            border: 1px solid #dfe1ff;
            border-radius: 16px;
            padding: clamp(24px, 3vw, 42px);
            margin-bottom: 20px;
            box-shadow: var(--shadow-md);
        }
        .app-hero::after {
            content: "";
            position: absolute;
            width: 180px;
            height: 180px;
            right: -65px;
            top: -85px;
            border-radius: 50%;
            background: rgba(139, 92, 246, 0.10);
            pointer-events: none;
        }
        .app-hero h1 {
            margin: 0 0 10px 0;
            font-size: 2rem;
            line-height: 1.15;
            letter-spacing: 0;
            color: var(--text-main);
        }
        .app-hero p { margin: 0; color: var(--text-muted); max-width: 920px; }
        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
            color: #5654d8 !important;
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .hero-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 16px;
        }
        .chip {
            display: inline-flex;
            align-items: center;
            min-height: 28px;
            padding: 5px 10px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid #d9dcff;
            color: #344054;
            font-size: 0.82rem;
            font-weight: 650;
        }
        .onboarding-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
            margin: 4px 0 24px 0;
        }
        .onboarding-strip.onboarding-four {
            grid-template-columns: repeat(4, minmax(0, 1fr));
        }
        .onboarding-item {
            display: grid;
            grid-template-columns: 32px 1fr;
            gap: 10px;
            padding: 14px 16px;
            min-width: 0;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: var(--shadow-sm);
            transition: transform 160ms ease, box-shadow 160ms ease;
        }
        .onboarding-item:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        .onboarding-item + .onboarding-item {
            border-left: 1px solid var(--border);
        }
        .onboarding-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 10px;
            background: var(--accent-gradient);
            color: #ffffff !important;
            font-weight: 800;
        }
        .onboarding-item strong {
            display: block;
            margin-bottom: 3px;
        }
        .onboarding-item p {
            color: var(--text-muted) !important;
            font-size: 0.84rem;
            line-height: 1.4;
            margin: 0;
        }
        .empty-state {
            background: #ffffff;
            border: 1px dashed #9fb3c8;
            border-radius: 16px;
            padding: 28px;
            margin: 12px 0 18px 0;
        }
        .empty-state strong {
            display: block;
            font-size: 1rem;
            margin-bottom: 5px;
        }
        .empty-state p {
            color: var(--text-muted) !important;
            margin: 0;
            line-height: 1.5;
        }
        .quality-list {
            margin: 8px 0 0 0;
            padding-left: 18px;
        }
        .quality-list li {
            color: var(--text-muted) !important;
            margin: 4px 0;
        }
        .soft-panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px 18px;
            margin: 10px 0 16px 0;
        }
        .insight-panel {
            background: linear-gradient(135deg, #ffffff, #f7f7ff);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px 16px;
            margin: 12px 0 18px 0;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .insight-panel strong {
            color: var(--text-main);
        }
        .insight-panel span {
            color: var(--text-muted) !important;
        }
        .completion-panel {
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
            margin: 18px 0 12px;
            padding: 22px 24px;
            background: linear-gradient(135deg, #eefbf3 0%, #ffffff 48%, #f1f1ff 100%);
            border: 1px solid #cdebd8;
            border-radius: 16px;
            box-shadow: var(--shadow-md);
        }
        .completion-panel::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 5px;
            background: linear-gradient(180deg, #22c55e, #5b5bf0);
        }
        .completion-copy {
            min-width: 0;
        }
        .completion-title {
            display: block;
            margin-bottom: 5px;
            color: var(--text-main) !important;
            font-family: "Plus Jakarta Sans", sans-serif;
            font-size: 1.06rem;
            font-weight: 800;
        }
        .completion-body {
            color: var(--text-muted) !important;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        .completion-cta {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            flex: 0 0 auto;
            min-height: 48px;
            padding: 12px 20px;
            border-radius: 12px;
            background: var(--accent-gradient);
            color: #ffffff !important;
            font-size: 0.92rem;
            font-weight: 800;
            text-decoration: none !important;
            box-shadow: 0 10px 22px rgba(91, 91, 240, 0.24);
            transition: transform 160ms ease, box-shadow 160ms ease;
        }
        .completion-cta:hover {
            color: #ffffff !important;
            text-decoration: none !important;
            transform: translateY(-2px);
            box-shadow: 0 14px 28px rgba(91, 91, 240, 0.30);
        }
        .section-title {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin: 24px 0 10px 0;
        }
        .section-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            border-radius: 10px;
            background: var(--accent-gradient);
            color: #ffffff !important;
            font-weight: 800;
            flex: 0 0 auto;
        }
        .section-title h2 {
            margin: 0;
            font-size: 1.12rem;
            line-height: 1.25;
        }
        .section-title p {
            margin: 3px 0 0 0;
            color: var(--text-muted) !important;
            font-size: 0.92rem;
        }
        .upload-note {
            background: #ffffff;
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent);
            border-radius: 12px;
            padding: 12px 14px;
            margin: 12px 0;
            color: var(--text-muted);
        }
        .mode-help {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px 16px;
            margin: 12px 0;
        }
        .mode-help strong { color: var(--text-main); }
        .mode-help p { margin: 4px 0 0 0; color: var(--text-muted) !important; }
        .entity-separator {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 76px;
            padding-top: 10px;
            color: var(--accent) !important;
            font-family: "Plus Jakarta Sans", sans-serif;
            font-size: 1.25rem;
            font-weight: 800;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--border);
            border-radius: 14px;
            background: var(--surface);
            box-shadow: var(--shadow-sm);
            transition: border-color 160ms ease, box-shadow 160ms ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #cfd1ff;
            box-shadow: var(--shadow-md);
        }
        .step-row {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 8px;
            margin: 12px 0 18px 0;
        }
        .step-pill {
            min-height: 72px;
            border: 1px solid var(--border);
            border-radius: 14px;
            background: #ffffff;
            padding: 12px;
            color: var(--text-muted);
            font-size: 0.84rem;
            box-shadow: var(--shadow-sm);
            transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
        }
        .step-pill:hover {
            transform: translateY(-2px);
            border-color: #cfd1ff;
            box-shadow: var(--shadow-md);
        }
        .step-pill strong { display: block; color: var(--text-main); margin-bottom: 5px; }
        .step-code {
            display: inline-block;
            color: #1d4ed8;
            font-weight: 800;
            margin-right: 4px;
        }
        .status-stepper {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 8px;
            margin: 12px 0 18px 0;
        }
        .status-step {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 11px 12px;
            min-height: 68px;
            box-shadow: var(--shadow-sm);
        }
        .status-step-title {
            display: block;
            font-weight: 800;
            margin-bottom: 6px;
        }
        .status-badge {
            display: inline-flex;
            padding: 4px 9px;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 800;
            text-transform: uppercase;
        }
        .status-ok, .status-cached { background: var(--success-soft); color: #13733a !important; }
        .status-running { background: var(--accent-soft); color: #4c48ce !important; }
        .status-error { background: var(--danger-soft); color: var(--danger) !important; }
        .status-pending, .status-skipped { background: #eef2f6; color: #667085 !important; }
        .quality-ok { color: var(--success); font-weight: 650; }
        .quality-warn { color: var(--warning); font-weight: 650; }
        .quality-bad { color: var(--danger); font-weight: 650; }
        div.stButton > button[kind="primary"] {
            background: var(--accent-gradient);
            border: 0;
            border-radius: 12px;
            min-height: 46px;
            font-weight: 700;
            color: #ffffff !important;
            box-shadow: 0 8px 20px rgba(91, 91, 240, 0.22);
            transition: transform 160ms ease, box-shadow 160ms ease;
        }
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #5558e8, #7c4de3);
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(91, 91, 240, 0.28);
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }
        div[data-testid="stDownloadButton"] button {
            border-radius: 12px;
            min-height: 42px;
            font-weight: 700;
        }
        div[data-testid="stDownloadButton"] button:hover,
        div.stButton > button:not([kind="primary"]):hover {
            border-color: var(--accent);
            color: var(--accent) !important;
            transform: translateY(-1px);
        }
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 6px;
            background: #eef0f7;
            border-radius: 12px;
            padding: 5px;
        }
        div[data-testid="stTabs"] button[role="tab"] {
            border-radius: 9px;
            padding: 9px 14px;
        }
        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            background: #ffffff;
            box-shadow: var(--shadow-sm);
        }
        div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            background-color: transparent;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            border-radius: 11px;
            transition: border-color 160ms ease, box-shadow 160ms ease;
        }
        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="input"] > div:focus-within,
        div[data-baseweb="textarea"] > div:focus-within {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(91, 91, 240, 0.12);
        }
        @media (max-width: 900px) {
            .step-row, .status-stepper { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .onboarding-strip { grid-template-columns: 1fr; }
            .onboarding-item + .onboarding-item {
                border-left: 0;
                border-top: 1px solid var(--border);
            }
            .app-hero h1 { font-size: 1.55rem; }
            .section-title { gap: 10px; }
        }
        @media (max-width: 640px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1rem;
            }
            div[data-testid="stHorizontalBlock"] {
                flex-wrap: wrap;
            }
            div[data-testid="column"] {
                flex: 1 1 100% !important;
                width: 100% !important;
                min-width: 100% !important;
            }
            .app-hero { padding: 20px; }
            .step-row, .status-stepper { grid-template-columns: 1fr; }
            .hero-actions { gap: 6px; }
            .chip { width: 100%; }
            .entity-separator { min-height: auto; padding: 0; }
            .completion-panel {
                align-items: stretch;
                flex-direction: column;
                gap: 16px;
                padding: 20px;
            }
            .completion-cta { width: 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header() -> None:
    st.markdown(
        """
        <div class="app-hero">
            <div class="eyebrow">Analisis kualitatif komparatif</div>
            <h1>Analisis Aspek Komparatif</h1>
            <p>Upload data pertanyaan dan jawaban, tuliskan hal yang dibandingkan, lalu sistem membantu menemukan tema/aspek utama dari jawaban responden.</p>
            <div class="hero-actions">
                <span class="chip">Upload CSV</span>
                <span class="chip">Tentukan perbandingan</span>
                <span class="chip">Lihat ringkasan aspek</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_results_header() -> None:
    st.markdown(
        """
        <div class="app-hero">
            <div class="eyebrow">Hasil yang siap ditinjau</div>
            <h1>Hasil Analisis</h1>
            <p>Lihat tema/aspek yang paling sering muncul, cek contoh pendapat pendukung, dan buka detail teknis hanya jika perlu meninjau prosesnya.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_onboarding() -> None:
    st.markdown(
        """
        <div class="onboarding-strip onboarding-four">
            <div class="onboarding-item">
                <span class="onboarding-number">1</span>
                <div><strong>Upload CSV</strong><p>Pilih file berisi kolom pertanyaan dan jawaban.</p></div>
            </div>
            <div class="onboarding-item">
                <span class="onboarding-number">2</span>
                <div><strong>Isi perbandingan</strong><p>Tuliskan hal-hal yang dibandingkan dalam pertanyaan.</p></div>
            </div>
            <div class="onboarding-item">
                <span class="onboarding-number">3</span>
                <div><strong>Sistem mengecek</strong><p>Data divalidasi otomatis sebelum analisis berjalan.</p></div>
            </div>
            <div class="onboarding-item">
                <span class="onboarding-number">4</span>
                <div><strong>Tinjau hasil</strong><p>Lihat daftar aspek, frekuensi, dan contoh pendapatnya.</p></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <strong>{title}</strong>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pipeline_overview() -> None:
    steps = [
        ("01", "Baca Data", "Sistem mengenali kolom pertanyaan dan jawaban."),
        ("02", "Pecah Jawaban", "Jawaban panjang dibagi menjadi pendapat kecil."),
        ("03", "Cek Bahasa", "Struktur kalimat dibantu dibaca oleh sistem."),
        ("04", "Cari Aspek", "Sistem mengambil hal yang sedang dibandingkan."),
        ("05", "Rapikan Label", "Nama aspek yang mirip digabung."),
        ("06", "Buat Ringkasan", "Tampilkan jumlah kemunculan dan contoh pendapat."),
    ]
    html = '<div class="step-row">'
    for code, title, body in steps:
        html += f'<div class="step-pill"><strong><span class="step-code">{code}</span>{title}</strong>{body}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_status_stepper(statuses: dict[str, str]) -> None:
    steps = [
        ("1", "Data siap", "raw_dataset"),
        ("2", "Pendapat dipisah", "opinion_units"),
        ("3", "Bahasa dicek", "pos_tagging"),
        ("4", "Aspek ditemukan", "candidate_codes"),
        ("5", "Label dirapikan", "candidate_normalization"),
        ("6", "Ringkasan jadi", "candidate_summary"),
    ]
    html = '<div class="status-stepper">'
    for code, title, key in steps:
        status = str(statuses.get(key, "pending")).lower()
        html += (
            '<div class="status-step">'
            f'<span class="status-step-title">{code} {title}</span>'
            f'<span class="status-badge status-{status}">{status}</span>'
            "</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_section_title(number: int, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="section-title">
            <span class="section-number">{number}</span>
            <div>
                <h2>{title}</h2>
                <p>{body}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(llm_api_key: str, llm_model: str, local_results_dir: Path, *, active: str = "run") -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">Analisis Aspek</div>
                <div class="sidebar-brand-subtitle">Bantu membaca pola jawaban dari pertanyaan komparatif.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="nav-label">Navigasi</div>', unsafe_allow_html=True)
        if active == "run":
            st.markdown('<div class="nav-active">Mulai Analisis<span class="nav-hint">Upload data dan isi perbandingan</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<a class="nav-link" href="/" target="_self"><span class="nav-link-title">Mulai Analisis</span><span class="nav-hint">Upload data dan isi perbandingan</span></a>', unsafe_allow_html=True)

        if active == "results":
            st.markdown('<div class="nav-active">Hasil Analisis<span class="nav-hint">Dashboard, tabel, dan download</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<a class="nav-link" href="/Hasil" target="_self"><span class="nav-link-title">Hasil Analisis</span><span class="nav-hint">Dashboard, tabel, dan download</span></a>', unsafe_allow_html=True)
        st.divider()
        st.header("Sistem")
        if llm_api_key:
            st.success("Koneksi AI aktif.")
        else:
            st.warning("API key belum diisi.")
        with st.expander("Detail teknis"):
            st.caption(f"Model: `{llm_model}`")
            st.caption(f"Folder hasil: `{local_results_dir}`")
        st.divider()
        st.markdown("**Cara pakai**")
        st.caption("Upload CSV, isi hal yang dibandingkan, mulai analisis, lalu buka halaman Hasil.")
        st.divider()
        st.markdown("**Output utama**")
        st.caption("Daftar aspek yang muncul, jumlah kemunculan, dan contoh jawaban pendukung.")
