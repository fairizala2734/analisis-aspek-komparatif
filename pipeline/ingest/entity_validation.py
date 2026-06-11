"""Preflight validation for user-defined comparison entities."""

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd

VALIDATION_COLUMNS = [
    "row_id",
    "question",
    "matched_entities",
    "entity_match_count",
    "entity_status",
    "comparative_status",
    "validation_status",
    "validation_reason",
]


@dataclass(frozen=True)
class ComparisonEntity:
    name: str
    aliases: tuple[str, ...] = ()

    @property
    def terms(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "aliases": list(self.aliases)}


def normalize_match_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def parse_comparison_entities(frame: pd.DataFrame) -> list[ComparisonEntity]:
    entities: list[ComparisonEntity] = []
    seen_terms: dict[str, str] = {}
    if frame is None or frame.empty:
        return entities

    for row in frame.to_dict(orient="records"):
        name = str(row.get("Hal yang dibandingkan", "") or "").strip()
        aliases_raw = str(row.get("Nama lain (opsional)", "") or "").strip()
        if not name:
            continue
        aliases = tuple(
            alias.strip()
            for alias in re.split(r"[,;]", aliases_raw)
            if alias.strip()
        )
        entity = ComparisonEntity(name=name, aliases=aliases)
        for term in entity.terms:
            normalized = normalize_match_text(term)
            if not normalized:
                continue
            owner = seen_terms.get(normalized)
            if owner and owner != name:
                raise ValueError(
                    f'Nama atau alias "{term}" dipakai oleh lebih dari satu hal yang dibandingkan.'
                )
            seen_terms[normalized] = name
        entities.append(entity)

    unique_names = {normalize_match_text(entity.name) for entity in entities}
    if len(unique_names) != len(entities):
        raise ValueError("Ada nama hal yang dibandingkan yang ditulis lebih dari satu kali.")
    return entities


def validate_entity_setup(entities: list[ComparisonEntity]) -> None:
    if len(entities) < 2:
        raise ValueError("Isi minimal dua hal yang ingin dibandingkan.")


def _contains_term(text: str, term: str) -> bool:
    normalized_term = normalize_match_text(term)
    if not normalized_term:
        return False
    return re.search(rf"(?:^|\s){re.escape(normalized_term)}(?:$|\s)", text) is not None


def match_entities(question: Any, entities: list[ComparisonEntity]) -> list[str]:
    normalized_question = normalize_match_text(question)
    return [
        entity.name
        for entity in entities
        if any(_contains_term(normalized_question, term) for term in entity.terms)
    ]


def canonicalize_entity(value: Any, entities: list[ComparisonEntity]) -> str:
    normalized = normalize_match_text(value)
    if not normalized:
        return ""
    for entity in entities:
        if any(normalized == normalize_match_text(term) for term in entity.terms):
            return entity.name
    return ""


ComparativeJudger = Callable[[int, str, list[str]], tuple[bool, str]]


def validate_comparative_rows(
    raw_df: pd.DataFrame,
    entities: list[ComparisonEntity],
    *,
    comparative_judger: ComparativeJudger | None = None,
    assume_comparative: bool = False,
    log_fn=None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    validate_entity_setup(entities)
    report_rows: list[dict[str, Any]] = []
    valid_ids: set[int] = set()

    for row in raw_df.to_dict(orient="records"):
        row_id = int(row["row_id"])
        question = str(row.get("question", "") or "")
        matched = match_entities(question, entities)
        entity_ok = len(matched) >= 2
        comparative_ok = False
        comparative_reason = ""

        if log_fn:
            matched_text = " | ".join(matched) if matched else "tidak ada"
            log_fn(
                f"Row {row_id}: pemeriksaan entity oleh sistem menemukan "
                f"{len(matched)} entity ({matched_text})."
            )

        if entity_ok and assume_comparative:
            comparative_ok = True
            comparative_reason = "Lolos validasi lewat bypass pemeriksaan bentuk pertanyaan."
            if log_fn:
                log_fn(f"Row {row_id}: pemeriksaan komparatif oleh LLM dilewati sesuai pengaturan.")
        elif entity_ok:
            if comparative_judger is None:
                raise RuntimeError(
                    "comparative_judger wajib diisi ketika pemeriksaan bentuk pertanyaan tidak dibypass."
                )
            comparative_ok, comparative_reason = comparative_judger(row_id, question, matched)
            comparative_ok = bool(comparative_ok)
            comparative_reason = str(comparative_reason or "").strip()

        if not entity_ok:
            reason = "Pertanyaan tidak menyebut minimal dua hal yang dibandingkan."
            if log_fn:
                log_fn(
                    f"Row {row_id}: ditolak sebelum pemeriksaan LLM karena "
                    "kurang dari dua entity ditemukan."
                )
        elif not comparative_ok:
            reason = comparative_reason or "LLM menilai pertanyaan ini belum komparatif."
        else:
            reason = comparative_reason or "Lolos validasi."
            valid_ids.add(row_id)

        report_rows.append(
            {
                "row_id": row_id,
                "question": question,
                "matched_entities": " | ".join(matched),
                "entity_match_count": len(matched),
                "entity_status": "matched" if entity_ok else "mismatch",
                "comparative_status": "comparative" if comparative_ok else "not_comparative",
                "validation_status": "accepted" if comparative_ok else "rejected",
                "validation_reason": reason,
            }
        )

    report = pd.DataFrame(report_rows, columns=VALIDATION_COLUMNS)
    valid = raw_df[raw_df["row_id"].astype(int).isin(valid_ids)].copy()
    return valid, report
