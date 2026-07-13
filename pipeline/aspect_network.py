"""Dataset-adaptive comparative aspect network outputs."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pipeline.ingest.csv_io import safe_read_csv, save_df
from pipeline.schemas import CANDIDATE_COLUMNS, NORMALIZED_SUMMARY_COLUMNS, OUTPUT_COLUMNS

NETWORK_PROFILE_FILE = "07_network_profile.json"
NETWORK_RECOMMENDATION_FILE = "07_network_recommendation.json"
NETWORK_NODES_FILE = "07_aspect_network_nodes.csv"
NETWORK_EDGES_FILE = "07_aspect_network_edges.csv"
NETWORK_INSIGHTS_FILE = "07_network_insights.json"

NETWORK_NODE_COLUMNS = [
    "node_id",
    "label",
    "type",
    "frequency",
    "source",
]

NETWORK_EDGE_COLUMNS = [
    "source",
    "target",
    "weight",
    "relation",
    "sample_opinion_units",
]

NETWORK_RECOMMENDATION_SYSTEM_PROMPT = """
You are a qualitative data visualization advisor.
Your task is to recommend a readable network configuration from a dataset profile.

Return only a JSON object with these keys:
- network_type: one of ["aspect_centered", "entity_aspect_position", "word_cooccurrence"]
- max_nodes: integer
- min_word_frequency: integer
- min_edge_weight: integer
- max_words_per_aspect: integer
- reason: short Indonesian explanation for non-technical researchers

Rules:
- Recommend the main overview network, not an exhaustive graph.
- Prefer "aspect_centered" when normalized candidate codes are available.
- Do not invent nodes, labels, or findings.
- Use the profile metrics to balance coverage and readability.
- Smaller datasets should use fewer nodes and lower thresholds.
- Larger datasets should use higher thresholds to avoid clutter.
""".strip()


RESOURCE_DIR = Path(__file__).resolve().parent / "resources"
STOPWORDS_ID_PATH = RESOURCE_DIR / "stopwords_id.txt"
STOPWORDS_SOURCE_URL = "https://github.com/stopwords-iso/stopwords-id"

# Extra visualization stopwords: generic comparison/evaluation verbs or modifiers
# that often dominate a graph but are less useful as standalone evidence nodes.
NETWORK_EXTRA_STOPWORDS = {
    "banding",
    "bernilai",
    "cenderung",
    "dibanding",
    "dibandingkan",
    "dibuat",
    "dibuatnya",
    "dikerjakan",
    "kurang",
    "lebih",
    "langsung",
    "memiliki",
    "membuat",
    "menjadi",
    "rendah",
    "secara",
    "tinggi",
}


def _load_stopwords() -> set[str]:
    stopwords = set(NETWORK_EXTRA_STOPWORDS)
    try:
        text = STOPWORDS_ID_PATH.read_text(encoding="utf-8")
    except OSError:
        return stopwords
    for word in re.split(r"\s+", text.strip()):
        word = word.strip().lower()
        if word:
            stopwords.add(word)
    return stopwords


GENERIC_STOPWORDS = _load_stopwords()


def _read(project_dir: Path, filename: str, columns: list[str] | None = None) -> pd.DataFrame:
    path = project_dir / filename
    if not path.exists():
        return pd.DataFrame(columns=columns or [])
    return safe_read_csv(path, columns)


def _split_cell(value: Any) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in re.split(r"\s*\|\s*|\s*\|\|\s*", str(value)) if part.strip()]


def _tokens(text: str, *, entity_terms: set[str] | None = None) -> list[str]:
    entity_terms = entity_terms or set()
    text = str(text).lower()
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9_]+", text)
    clean: list[str] = []
    for word in words:
        word = word.strip("_")
        if len(word) < 3 or word.isdigit():
            continue
        if word in GENERIC_STOPWORDS or word in entity_terms:
            continue
        clean.append(word)
    return clean


def _stable_id(prefix: str, label: str) -> str:
    digest = hashlib.sha1(label.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


def build_network_profile(project_dir: Path) -> dict[str, Any]:
    final_df = _read(project_dir, "06_candidate_summary_normalized.csv", NORMALIZED_SUMMARY_COLUMNS)
    candidate_df = _read(project_dir, "03_candidate_codes.csv", CANDIDATE_COLUMNS)
    opinion_df = _read(project_dir, "02_opinion_units.csv", OUTPUT_COLUMNS)

    entity_terms: set[str] = set()
    if not final_df.empty:
        for column in ["main_entities", "counterpart_entities"]:
            if column in final_df.columns:
                for value in final_df[column].dropna().astype(str):
                    for entity in _split_cell(value):
                        entity_terms.update(_tokens(entity))

    all_text: list[str] = []
    if not opinion_df.empty and "opinion_unit" in opinion_df.columns:
        all_text.extend(opinion_df["opinion_unit"].dropna().astype(str).tolist())
    elif not final_df.empty and "sample_opinion_units" in final_df.columns:
        all_text.extend(final_df["sample_opinion_units"].dropna().astype(str).tolist())

    token_counts = Counter()
    text_lengths: list[int] = []
    for text in all_text:
        row_tokens = _tokens(text, entity_terms=entity_terms)
        token_counts.update(row_tokens)
        if row_tokens:
            text_lengths.append(len(row_tokens))

    top_codes: list[dict[str, Any]] = []
    if not final_df.empty:
        sortable = final_df.copy()
        sortable["frequency_num"] = pd.to_numeric(sortable.get("frequency", 0), errors="coerce").fillna(0)
        for row in sortable.sort_values("frequency_num", ascending=False).head(20).to_dict(orient="records"):
            top_codes.append(
                {
                    "normalized_candidate_code": str(row.get("normalized_candidate_code", "")),
                    "frequency": int(row.get("frequency_num", 0) or 0),
                    "sample_opinion_units": str(row.get("sample_opinion_units", ""))[:350],
                }
            )

    profile = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_files": [
            "02_opinion_units.csv",
            "03_candidate_codes.csv",
            "06_candidate_summary_normalized.csv",
        ],
        "stopwords": {
            "source": STOPWORDS_SOURCE_URL,
            "path": str(STOPWORDS_ID_PATH),
            "count": len(GENERIC_STOPWORDS),
        },
        "opinion_units": int(len(opinion_df)),
        "raw_candidate_codes": (
            int(candidate_df["candidate_code"].nunique()) if "candidate_code" in candidate_df else 0
        ),
        "normalized_candidate_codes": int(len(final_df)),
        "unique_words": int(len(token_counts)),
        "average_opinion_unit_words": round(sum(text_lengths) / max(1, len(text_lengths)), 2),
        "top_words": [{"word": word, "frequency": int(freq)} for word, freq in token_counts.most_common(30)],
        "top_normalized_candidate_codes": top_codes,
    }
    return profile


def fallback_recommendation(profile: dict[str, Any]) -> dict[str, Any]:
    opinion_units = int(profile.get("opinion_units") or 0)
    aspects = int(profile.get("normalized_candidate_codes") or 0)
    unique_words = int(profile.get("unique_words") or 0)

    if opinion_units <= 20 or aspects <= 8:
        max_nodes = min(35, max(18, aspects * 5 or 20))
        min_word_frequency = 1
        min_edge_weight = 1
        words_per_aspect = 6
    elif opinion_units <= 150:
        max_nodes = min(45, max(28, min(aspects * 2, 42)))
        min_word_frequency = 3 if unique_words > 80 else 2
        min_edge_weight = 1
        words_per_aspect = 5
    else:
        max_nodes = min(50, max(34, min(aspects, 48)))
        min_word_frequency = 4 if unique_words > 250 else 3
        min_edge_weight = 2
        words_per_aspect = 4

    return {
        "network_type": "aspect_centered",
        "max_nodes": int(max_nodes),
        "min_word_frequency": int(min_word_frequency),
        "min_edge_weight": int(min_edge_weight),
        "max_words_per_aspect": int(words_per_aspect),
        "reason": (
            "Rekomendasi fallback berbasis ukuran dataset: jumlah node dibatasi agar aspek utama "
            "tetap terlihat tanpa membuat jaringan terlalu padat."
        ),
        "source": "python_fallback",
    }


def sanitize_recommendation(raw: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    fallback = fallback_recommendation(profile)
    network_type = str(raw.get("network_type") or fallback["network_type"]).strip()
    if network_type not in {"aspect_centered", "entity_aspect_position", "word_cooccurrence"}:
        network_type = "aspect_centered"
    aspects = max(1, int(profile.get("normalized_candidate_codes") or 1))
    max_nodes = int(raw.get("max_nodes") or fallback["max_nodes"])
    max_nodes = min(150, max(min(25, aspects), max_nodes))
    min_word_frequency = min(20, max(1, int(raw.get("min_word_frequency") or fallback["min_word_frequency"])))
    min_edge_weight = min(20, max(1, int(raw.get("min_edge_weight") or fallback["min_edge_weight"])))
    max_words_per_aspect = min(
        15,
        max(1, int(raw.get("max_words_per_aspect") or fallback["max_words_per_aspect"])),
    )
    reason = str(raw.get("reason") or fallback["reason"]).strip()
    return {
        "network_type": network_type,
        "max_nodes": max_nodes,
        "min_word_frequency": min_word_frequency,
        "min_edge_weight": min_edge_weight,
        "max_words_per_aspect": max_words_per_aspect,
        "reason": reason[:1200],
        "source": str(raw.get("source") or "llm_recommendation"),
    }


def get_network_recommendation(
    profile: dict[str, Any],
    *,
    recommender: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if recommender is None:
        return fallback_recommendation(profile)
    try:
        result = recommender(profile)
        if isinstance(result, dict):
            result.setdefault("source", "llm_recommendation")
            return sanitize_recommendation(result, profile)
    except Exception as exc:
        fallback = fallback_recommendation(profile)
        fallback["source"] = "python_fallback_after_llm_error"
        fallback["llm_error"] = str(exc)[:500]
        return fallback
    return fallback_recommendation(profile)


def build_aspect_network(
    project_dir: Path,
    recommendation: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    final_df = _read(project_dir, "06_candidate_summary_normalized.csv", NORMALIZED_SUMMARY_COLUMNS)
    if final_df.empty:
        empty_nodes = pd.DataFrame(columns=NETWORK_NODE_COLUMNS)
        empty_edges = pd.DataFrame(columns=NETWORK_EDGE_COLUMNS)
        return empty_nodes, empty_edges, {
            "status": "empty",
            "reason": "06_candidate_summary_normalized.csv kosong",
        }

    entity_terms: set[str] = set()
    for column in ["main_entities", "counterpart_entities"]:
        if column in final_df.columns:
            for value in final_df[column].dropna().astype(str):
                for entity in _split_cell(value):
                    entity_terms.update(_tokens(entity))

    working = final_df.copy()
    working["frequency_num"] = (
        pd.to_numeric(working.get("frequency", 0), errors="coerce").fillna(0).astype(int)
    )
    working = working.sort_values(["frequency_num", "normalized_candidate_code"], ascending=[False, True])

    max_nodes = int(recommendation.get("max_nodes") or 50)
    min_word_frequency = int(recommendation.get("min_word_frequency") or 1)
    min_edge_weight = int(recommendation.get("min_edge_weight") or 1)
    max_words_per_aspect = int(recommendation.get("max_words_per_aspect") or 6)

    aspect_budget = min(
        len(working),
        max(1, min(24, max(6, max_nodes // 2))),
    )
    selected_aspects = working.head(aspect_budget)

    node_rows: list[dict[str, Any]] = []
    edge_rows: list[dict[str, Any]] = []
    word_node_ids: dict[str, str] = {}
    word_frequencies: Counter[str] = Counter()
    aspect_word_counts: dict[str, Counter[str]] = {}

    for row in selected_aspects.to_dict(orient="records"):
        aspect = str(row.get("normalized_candidate_code", "")).strip()
        if not aspect:
            continue
        text_parts = [
            str(row.get("sample_opinion_units", "")),
            str(row.get("main_positions", "")),
            str(row.get("counterpart_positions", "")),
            str(row.get("original_candidate_codes", "")),
        ]
        counter = Counter(_tokens(" ".join(text_parts), entity_terms=entity_terms))
        aspect_tokens = set(_tokens(aspect))
        for token in list(counter):
            if token in aspect_tokens:
                counter.pop(token, None)
        aspect_word_counts[aspect] = counter
        word_frequencies.update(counter)

    available_word_slots = max(0, max_nodes - len(selected_aspects))
    selected_words: set[str] = set()
    target_word_nodes = min(
        available_word_slots,
        max(4, min(12, len(selected_aspects))),
    )
    threshold_candidates: list[int] = []
    for threshold in [min_word_frequency, 4, 3, 2, 1]:
        threshold = max(1, min(int(threshold), int(min_word_frequency)))
        if threshold not in threshold_candidates:
            threshold_candidates.append(threshold)

    effective_min_word_frequency = min_word_frequency
    for threshold in threshold_candidates:
        candidate_words: set[str] = set()
        for _aspect, counter in aspect_word_counts.items():
            for word, count in counter.most_common(max_words_per_aspect):
                if count < threshold:
                    continue
                candidate_words.add(word)
        selected_words = candidate_words
        effective_min_word_frequency = threshold
        if len(selected_words) >= target_word_nodes or threshold == threshold_candidates[-1]:
            break

    word_limit = min(available_word_slots, target_word_nodes)
    if len(selected_words) > word_limit:
        selected_words = {
            word
            for word, _ in word_frequencies.most_common(word_limit)
            if word in selected_words
        }

    effective_min_edge_weight = min_edge_weight
    if effective_min_word_frequency < min_word_frequency:
        effective_min_edge_weight = min(
            min_edge_weight,
            max(1, effective_min_word_frequency // 2),
        )

    for row in selected_aspects.to_dict(orient="records"):
        aspect = str(row.get("normalized_candidate_code", "")).strip()
        if not aspect:
            continue
        node_rows.append(
            {
                "node_id": _stable_id("aspect", aspect),
                "label": aspect,
                "type": "aspect",
                "frequency": int(row.get("frequency_num", 0) or 0),
                "source": "06_candidate_summary_normalized.csv",
            }
        )

    for word in sorted(selected_words):
        node_id = _stable_id("word", word)
        word_node_ids[word] = node_id
        node_rows.append(
            {
                "node_id": node_id,
                "label": word,
                "type": "word",
                "frequency": int(word_frequencies[word]),
                "source": "sample_opinion_units",
            }
        )

    for row in selected_aspects.to_dict(orient="records"):
        aspect = str(row.get("normalized_candidate_code", "")).strip()
        if not aspect:
            continue
        source_id = _stable_id("aspect", aspect)
        samples = str(row.get("sample_opinion_units", ""))
        for word, count in aspect_word_counts.get(aspect, Counter()).most_common(max_words_per_aspect):
            if word not in selected_words or count < effective_min_edge_weight:
                continue
            edge_rows.append(
                {
                    "source": source_id,
                    "target": word_node_ids[word],
                    "weight": int(count),
                    "relation": "aspect_support_word",
                    "sample_opinion_units": samples[:900],
                }
            )

    nodes_df = pd.DataFrame(node_rows).drop_duplicates("node_id").reindex(columns=NETWORK_NODE_COLUMNS)
    edges_df = pd.DataFrame(edge_rows).reindex(columns=NETWORK_EDGE_COLUMNS)
    node_count = len(nodes_df)
    edge_count = len(edges_df)
    density = 0.0
    if node_count > 1:
        density = round((2 * edge_count) / (node_count * (node_count - 1)), 4)
    represented_aspects = int((nodes_df["type"] == "aspect").sum()) if not nodes_df.empty else 0
    insights = {
        "status": "ok",
        "network_type": "aspect_centered",
        "node_count": node_count,
        "edge_count": edge_count,
        "density": density,
        "represented_aspects": represented_aspects,
        "coverage_aspect_ratio": round(represented_aspects / max(1, len(final_df)), 4),
        "requested_min_word_frequency": min_word_frequency,
        "effective_min_word_frequency": effective_min_word_frequency,
        "requested_min_edge_weight": min_edge_weight,
        "effective_min_edge_weight": effective_min_edge_weight,
        "stopwords_count": len(GENERIC_STOPWORDS),
        "top_nodes": nodes_df.sort_values("frequency", ascending=False).head(10).to_dict(orient="records"),
        "top_edges": edges_df.sort_values("weight", ascending=False).head(10).to_dict(orient="records")
        if not edges_df.empty
        else [],
    }
    return nodes_df, edges_df, insights


def build_aspect_network_outputs(
    project_dir: Path,
    *,
    recommender: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    force: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    nodes_path = project_dir / NETWORK_NODES_FILE
    edges_path = project_dir / NETWORK_EDGES_FILE
    profile_path = project_dir / NETWORK_PROFILE_FILE
    recommendation_path = project_dir / NETWORK_RECOMMENDATION_FILE
    insights_path = project_dir / NETWORK_INSIGHTS_FILE
    has_cached_outputs = (
        nodes_path.exists()
        and edges_path.exists()
        and profile_path.exists()
        and recommendation_path.exists()
    )
    if not force and has_cached_outputs:
        nodes_df = safe_read_csv(nodes_path, NETWORK_NODE_COLUMNS)
        edges_df = safe_read_csv(edges_path, NETWORK_EDGE_COLUMNS)
        try:
            recommendation = json.loads(recommendation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            recommendation = {}
        try:
            insights = json.loads(insights_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            insights = {}
        return nodes_df, edges_df, recommendation, insights

    profile = build_network_profile(project_dir)
    recommendation = get_network_recommendation(profile, recommender=recommender)
    nodes_df, edges_df, insights = build_aspect_network(project_dir, recommendation)

    profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    recommendation_path.write_text(json.dumps(recommendation, ensure_ascii=False, indent=2), encoding="utf-8")
    insights_path.write_text(json.dumps(insights, ensure_ascii=False, indent=2), encoding="utf-8")
    save_df(nodes_df, nodes_path)
    save_df(edges_df, edges_path)
    return nodes_df, edges_df, recommendation, insights


def circular_layout(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> dict[str, tuple[float, float]]:
    if nodes_df.empty:
        return {}
    aspect_ids = nodes_df.loc[nodes_df["type"] == "aspect", "node_id"].astype(str).tolist()
    word_ids = nodes_df.loc[nodes_df["type"] != "aspect", "node_id"].astype(str).tolist()
    positions: dict[str, tuple[float, float]] = {}
    aspect_count = max(1, len(aspect_ids))
    radius = 1.0 if aspect_count <= 8 else 1.35
    for idx, node_id in enumerate(aspect_ids):
        angle = (2 * math.pi * idx) / aspect_count
        positions[node_id] = (radius * math.cos(angle), radius * math.sin(angle))

    neighbor_map: dict[str, list[str]] = defaultdict(list)
    for row in edges_df.to_dict(orient="records"):
        neighbor_map[str(row.get("target"))].append(str(row.get("source")))

    for idx, node_id in enumerate(word_ids):
        parents = [parent for parent in neighbor_map.get(node_id, []) if parent in positions]
        if parents:
            x = sum(positions[parent][0] for parent in parents) / len(parents)
            y = sum(positions[parent][1] for parent in parents) / len(parents)
            base_angle = math.atan2(y, x) if x or y else (2 * math.pi * idx) / max(1, len(word_ids))
        else:
            base_angle = (2 * math.pi * idx) / max(1, len(word_ids))
        offset = 0.35 + (idx % 5) * 0.08
        positions[node_id] = (
            (radius + offset) * math.cos(base_angle + 0.12 * (idx % 3)),
            (radius + offset) * math.sin(base_angle + 0.12 * (idx % 3)),
        )
    return positions
