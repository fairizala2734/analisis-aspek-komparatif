"""Lazy Stanza loading and POS/noun formatting."""

import re
from functools import lru_cache
from typing import Any

import pandas as pd


@lru_cache(maxsize=4)
def load_stanza_pipeline(lang: str = "id", auto_download: bool = True):
    try:
        import stanza
    except Exception as exc:
        raise RuntimeError(
            "Library stanza belum terpasang. Jalankan: pip install -r requirements.txt"
        ) from exc

    try:
        return stanza.Pipeline(
            lang=lang,
            processors="tokenize,pos,lemma",
            use_gpu=False,
            verbose=False,
        )
    except Exception as first_error:
        if auto_download:
            try:
                stanza.download(lang, processors="tokenize,pos,lemma", verbose=False)
                return stanza.Pipeline(
                    lang=lang,
                    processors="tokenize,pos,lemma",
                    use_gpu=False,
                    verbose=False,
                )
            except Exception as second_error:
                raise RuntimeError(
                    f"Gagal memuat/download model Stanza bahasa '{lang}'. Error: {second_error}"
                ) from second_error
        raise RuntimeError(
            f"Gagal memuat model Stanza bahasa '{lang}'. "
            f"Aktifkan auto-download atau jalankan stanza.download('{lang}') sekali."
        ) from first_error


def format_pos_and_nouns(text: Any, nlp) -> tuple[str, str]:
    value = "" if text is None or (isinstance(text, float) and pd.isna(text)) else str(text).strip()
    if not value:
        return "", ""

    document = nlp(value)
    pos_items: list[str] = []
    noun_phrases: list[str] = []
    for sentence in document.sentences:
        words = sentence.words
        current: list[str] = []
        for word in words:
            token = (word.text or "").strip()
            upos = (word.upos or "X").strip()
            lemma = (word.lemma or token).strip()
            if token:
                pos_items.append(f"{token}/{upos}")
            if upos in {"NOUN", "PROPN"}:
                current.append(lemma.lower())
            elif current:
                phrase = " ".join(current).strip()
                if phrase:
                    noun_phrases.append(phrase)
                current = []
        if current:
            phrase = " ".join(current).strip()
            if phrase:
                noun_phrases.append(phrase)
        for word in words:
            if (word.upos or "") in {"NOUN", "PROPN"}:
                noun = (word.lemma or word.text or "").strip().lower()
                if noun:
                    noun_phrases.append(noun)

    seen: set[str] = set()
    clean_phrases: list[str] = []
    for phrase in noun_phrases:
        phrase = re.sub(r"\s+", " ", phrase).strip()
        if phrase and phrase not in seen:
            seen.add(phrase)
            clean_phrases.append(phrase)
    return " | ".join(pos_items), " | ".join(clean_phrases)
