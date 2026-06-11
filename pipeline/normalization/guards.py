"""Domain-agnostic structural guards for normalization output."""

import re
import unicodedata
from collections import defaultdict
from typing import Any


def norm_tokens(value: Any) -> list[str]:
    normalized = unicodedata.normalize("NFKC", str(value)).lower()
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    return [token for token in normalized.split() if token]


def derive_generic_heads_from_data(
    codes: list[str],
    min_distinct_modifiers: int = 3,
) -> list[str]:
    head_modifiers: dict[str, set[str]] = defaultdict(set)
    for code in codes:
        tokens = norm_tokens(code)
        if len(tokens) >= 2:
            head_modifiers[tokens[0]].add(" ".join(tokens[1:]))
    return sorted(
        head
        for head, modifiers in head_modifiers.items()
        if len(modifiers) >= min_distinct_modifiers
    )


def detect_overmerged_labels(
    mappings: dict[str, dict[str, str]],
) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for original, metadata in mappings.items():
        label = str(metadata.get("normalized_candidate_code", "")).strip()
        groups[label].append(original)

    flagged: dict[str, list[str]] = {}
    for label, members in groups.items():
        unique_members = sorted(set(member for member in members if member))
        label_tokens = set(norm_tokens(label))
        if len(unique_members) < 2 or not label_tokens:
            continue
        head_of_all = all(
            label_tokens.issubset(set(norm_tokens(member)))
            for member in unique_members
        )
        residuals = [
            tuple(sorted(set(norm_tokens(member)) - label_tokens))
            for member in unique_members
        ]
        distinct_residuals = {residual for residual in residuals if residual}
        if head_of_all and len(distinct_residuals) >= 2:
            flagged[label] = unique_members
    return flagged
