"""User-friendly controls for defining compared entities."""

import pandas as pd
import streamlit as st

ENTITY_INPUT_COLUMNS = ["Hal yang dibandingkan", "Nama lain (opsional)"]
ENTITY_COUNT_KEY = "comparison_entity_count"


def _add_entity_field() -> None:
    st.session_state[ENTITY_COUNT_KEY] = st.session_state.get(ENTITY_COUNT_KEY, 2) + 1


def _remove_entity_field() -> None:
    current = st.session_state.get(ENTITY_COUNT_KEY, 2)
    st.session_state[ENTITY_COUNT_KEY] = max(2, current - 1)


def render_comparison_entity_input() -> pd.DataFrame:
    st.caption(
        "Tuliskan minimal dua hal yang dibandingkan dalam pertanyaan. Tambahkan nama lain "
        "hanya jika responden mungkin memakai singkatan atau sebutan berbeda."
    )
    entity_count = st.session_state.setdefault(ENTITY_COUNT_KEY, 2)
    rows: list[dict[str, str]] = []

    # Keep the comparison readable by wrapping after three fields on wide screens.
    for group_start in range(0, entity_count, 3):
        group_end = min(group_start + 3, entity_count)
        group_size = group_end - group_start
        widths: list[float] = []
        for position in range(group_size):
            widths.append(5)
            if position < group_size - 1:
                widths.append(0.7)

        columns = st.columns(widths, vertical_alignment="center")
        column_index = 0
        for entity_index in range(group_start, group_end):
            with columns[column_index]:
                name = st.text_input(
                    f"Hal {entity_index + 1}",
                    key=f"comparison_entity_name_{entity_index}",
                    placeholder="Contoh: batik tulis",
                ).strip()
                aliases = st.text_input(
                    f"Nama lain hal {entity_index + 1} (opsional)",
                    key=f"comparison_entity_aliases_{entity_index}",
                    placeholder="Contoh: tulis, handmade",
                    help="Pisahkan beberapa nama lain dengan koma.",
                ).strip()
            rows.append(
                {
                    "Hal yang dibandingkan": name,
                    "Nama lain (opsional)": aliases,
                }
            )
            column_index += 1
            if entity_index < group_end - 1:
                with columns[column_index]:
                    st.markdown('<div class="entity-separator">&amp;</div>', unsafe_allow_html=True)
                column_index += 1

    add_column, remove_column, spacer = st.columns([1.6, 1.6, 6.8])
    with add_column:
        st.button(
            "+ Tambah hal",
            key="add_comparison_entity",
            on_click=_add_entity_field,
            width="stretch",
        )
    with remove_column:
        st.button(
            "Hapus terakhir",
            key="remove_comparison_entity",
            on_click=_remove_entity_field,
            disabled=entity_count <= 2,
            width="stretch",
        )

    return pd.DataFrame(rows, columns=ENTITY_INPUT_COLUMNS)
