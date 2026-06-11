"""User-friendly controls for defining compared entities."""

import pandas as pd
import streamlit as st

ENTITY_INPUT_COLUMNS = ["Hal yang dibandingkan", "Nama lain (opsional)"]


def render_comparison_entity_input() -> pd.DataFrame:
    st.caption(
        "Isi minimal dua hal. Nama lain dipakai jika pertanyaan menggunakan singkatan "
        "atau penyebutan berbeda, pisahkan dengan koma."
    )
    initial = pd.DataFrame(
        [
            {"Hal yang dibandingkan": "", "Nama lain (opsional)": ""},
            {"Hal yang dibandingkan": "", "Nama lain (opsional)": ""},
        ],
        columns=ENTITY_INPUT_COLUMNS,
    )
    return st.data_editor(
        initial,
        column_config={
            "Hal yang dibandingkan": st.column_config.TextColumn(
                "Hal yang dibandingkan",
                help='Contoh: "batik tulis" atau "batik cap".',
                required=True,
            ),
            "Nama lain (opsional)": st.column_config.TextColumn(
                "Nama lain (opsional)",
                help='Contoh: "tulis, handmade" untuk batik tulis.',
            ),
        },
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        key="comparison_entities_editor",
    )
