from pathlib import Path

import streamlit as st


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-bg: #f6f8fb;
            --surface: #ffffff;
            --surface-soft: #f1f5f9;
            --border: #d9e2ec;
            --text-main: #182230;
            --text-muted: #536579;
            --accent: #2563eb;
            --accent-dark: #1d4ed8;
            --accent-soft: #eaf2ff;
            --success: #0f766e;
            --warning: #b45309;
            --danger: #b91c1c;
        }
        .stApp { background: var(--app-bg); color: var(--text-main); }
        [data-testid="stSidebarNav"] { display: none; }
        .main .block-container {
            max-width: 1240px;
            padding-top: 2rem;
            padding-bottom: 3rem;
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
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        }
        button[role="tab"] *,
        div[data-testid="stTabs"] * {
            color: var(--text-main);
        }
        section[data-testid="stSidebar"] {
            background: #f0f5fb;
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
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 14px;
            margin-bottom: 14px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .sidebar-brand-title {
            font-weight: 800;
            font-size: 1rem;
            margin-bottom: 4px;
            color: var(--text-main);
        }
        .sidebar-brand-subtitle {
            color: var(--text-muted) !important;
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
            border: 1px solid #bcd4f6;
            border-left: 4px solid var(--accent);
            border-radius: 8px;
            padding: 10px 11px;
            margin: 6px 0;
            color: var(--text-main);
            font-weight: 800;
            box-shadow: 0 1px 2px rgba(37, 99, 235, 0.08);
        }
        .nav-link {
            display: block;
            background: transparent;
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 10px 11px;
            margin: 6px 0;
            color: var(--text-main) !important;
            font-weight: 750;
            text-decoration: none !important;
        }
        .nav-link:hover {
            background: #ffffff;
            border-color: var(--border);
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
            border-radius: 8px;
        }
        div[data-testid="stAlert"] * {
            color: var(--text-main) !important;
        }
        div[data-testid="stFileUploader"] section {
            background: #ffffff;
            border: 1px dashed #9fb3c8;
            border-radius: 8px;
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
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetricLabel"] p { color: var(--text-muted); font-size: 0.86rem; }
        div[data-testid="stMetricValue"] { color: var(--text-main); font-weight: 700; }
        .app-hero {
            background:
                linear-gradient(135deg, rgba(255,255,255,0.96) 0%, rgba(242,247,255,0.96) 56%, rgba(238,250,247,0.96) 100%),
                radial-gradient(circle at 92% 10%, rgba(37,99,235,0.10), transparent 28%);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 28px 30px;
            margin-bottom: 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
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
            color: #1d4ed8;
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
            background: #ffffff;
            border: 1px solid #cfe0f5;
            color: #334155;
            font-size: 0.82rem;
            font-weight: 650;
        }
        .onboarding-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            margin: 4px 0 20px 0;
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
            border-radius: 8px;
            background: var(--accent-soft);
            color: #1d4ed8 !important;
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
            border-radius: 8px;
            padding: 22px;
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
            border-radius: 8px;
            padding: 16px 18px;
            margin: 10px 0 16px 0;
        }
        .insight-panel {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 8px;
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
            border-radius: 8px;
            background: var(--accent-soft);
            color: #1d4ed8;
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
            border-radius: 8px;
            padding: 12px 14px;
            margin: 12px 0;
            color: var(--text-muted);
        }
        .mode-help {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 16px;
            margin: 12px 0;
        }
        .mode-help strong { color: var(--text-main); }
        .mode-help p { margin: 4px 0 0 0; color: var(--text-muted) !important; }
        .step-row {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 8px;
            margin: 12px 0 18px 0;
        }
        .step-pill {
            min-height: 72px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: #ffffff;
            padding: 12px;
            color: var(--text-muted);
            font-size: 0.84rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
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
            border-radius: 8px;
            padding: 11px 12px;
            min-height: 68px;
        }
        .status-step-title {
            display: block;
            font-weight: 800;
            margin-bottom: 6px;
        }
        .status-badge {
            display: inline-flex;
            padding: 3px 7px;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 800;
            text-transform: uppercase;
        }
        .status-ok, .status-cached { background: #dcfce7; color: #166534 !important; }
        .status-running { background: #dbeafe; color: #1d4ed8 !important; }
        .status-error { background: #fee2e2; color: #b91c1c !important; }
        .status-pending, .status-skipped { background: #e2e8f0; color: #475569 !important; }
        .quality-ok { color: var(--success); font-weight: 650; }
        .quality-warn { color: var(--warning); font-weight: 650; }
        .quality-bad { color: var(--danger); font-weight: 650; }
        div.stButton > button[kind="primary"] {
            background: var(--accent);
            border-color: var(--accent);
            border-radius: 8px;
            min-height: 46px;
            font-weight: 700;
        }
        div.stButton > button[kind="primary"]:hover {
            background: var(--accent-dark);
            border-color: var(--accent-dark);
        }
        div[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; }
        div[data-testid="stDownloadButton"] button {
            border-radius: 8px;
            min-height: 42px;
            font-weight: 700;
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
            <p>Bantu peneliti membaca data pertanyaan-jawaban komparatif: sistem memecah jawaban menjadi unit pendapat, mengambil aspek yang dibandingkan, menyatukan label serupa, lalu menyiapkan ringkasan yang mudah ditinjau.</p>
            <div class="hero-actions">
                <span class="chip">CSV Q&A</span>
                <span class="chip">Candidate code netral</span>
                <span class="chip">Ringkasan ternormalisasi</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_results_header() -> None:
    st.markdown(
        """
        <div class="app-hero">
            <div class="eyebrow">Dashboard hasil</div>
            <h1>Hasil Analisis</h1>
            <p>Tinjau ringkasan aspek, mapping normalisasi, data pendapat, dan catatan error dari run yang sudah tersimpan tanpa menjalankan ulang proses.</p>
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
                <div><strong>Periksa data</strong><p>Sistem menolak pertanyaan yang tidak cocok.</p></div>
            </div>
            <div class="onboarding-item">
                <span class="onboarding-number">4</span>
                <div><strong>Tinjau hasil</strong><p>Buka ringkasan akhir, mapping, dan catatan kualitas.</p></div>
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
        ("01", "Baca Data", "Rapikan kolom pertanyaan dan jawaban."),
        ("02", "Unit Pendapat", "Pecah jawaban menjadi klaim kecil."),
        ("02c", "Struktur Bahasa", "Bantu identifikasi frasa aspek."),
        ("03", "Aspek", "Ambil candidate_code netral posisi."),
        ("05", "Normalisasi", "Satukan label yang maknanya sama."),
        ("06", "Ringkasan", "Tampilkan frekuensi dan contoh."),
    ]
    html = '<div class="step-row">'
    for code, title, body in steps:
        html += f'<div class="step-pill"><strong><span class="step-code">{code}</span>{title}</strong>{body}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_status_stepper(statuses: dict[str, str]) -> None:
    steps = [
        ("01", "Raw", "raw_dataset"),
        ("02", "Opinion", "opinion_units"),
        ("02c", "POS", "pos_tagging"),
        ("03", "Candidate", "candidate_codes"),
        ("05", "Normalisasi", "candidate_normalization"),
        ("06", "Ringkasan", "candidate_summary"),
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
                <div class="sidebar-brand-subtitle">Tool bantu coding kualitatif untuk data tanya-jawab komparatif.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="nav-label">Navigasi</div>', unsafe_allow_html=True)
        if active == "run":
            st.markdown('<div class="nav-active">Run Analisis<span class="nav-hint">Upload CSV dan jalankan pipeline</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<a class="nav-link" href="/"><span class="nav-link-title">Run Analisis</span><span class="nav-hint">Upload CSV dan jalankan pipeline</span></a>', unsafe_allow_html=True)

        if active == "results":
            st.markdown('<div class="nav-active">Hasil Analisis<span class="nav-hint">Dashboard, tabel, dan download</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<a class="nav-link" href="/Hasil"><span class="nav-link-title">Hasil Analisis</span><span class="nav-hint">Dashboard, tabel, dan download</span></a>', unsafe_allow_html=True)
        st.divider()
        st.header("Sistem")
        if llm_api_key:
            st.success("OpenRouter API key aktif.")
        else:
            st.warning("OPENROUTER_API_KEY belum diisi.")
        st.caption(f"Model: `{llm_model}`")
        st.caption(f"Hasil: `{local_results_dir}`")
        st.divider()
        st.markdown("**Cara pakai**")
        st.caption("Upload CSV, pastikan kolom benar, pilih mode analisis, lalu buka halaman Hasil.")
        st.divider()
        st.markdown("**Output utama**")
        st.caption("Ringkasan aspek komparatif ternormalisasi, lengkap dengan frekuensi, posisi, dan contoh opinion unit.")
