"""Prompt versions and reproducible hashes."""

import hashlib
from dataclasses import dataclass

from llm.prompts.candidate_codes import CANDIDATE_CODE_SYSTEM_PROMPT
from llm.prompts.comparative_validation import COMPARATIVE_VALIDATION_SYSTEM_PROMPT
from llm.prompts.entity_context import ENTITY_CONTEXT_RULES
from llm.prompts.normalization import CANDIDATE_NORMALIZATION_SYSTEM_PROMPT
from llm.prompts.opinion_units import OPINION_UNITS_SYSTEM_PROMPT
from llm.prompts.relabel import RELABEL_SYSTEM_PROMPT


@dataclass(frozen=True)
class PromptSpec:
    name: str
    version: str
    text: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


PROMPTS = {
    "opinion_units": PromptSpec(
        "opinion_units",
        "v12_user_defined_entity_context",
        f"{OPINION_UNITS_SYSTEM_PROMPT}\n\n{ENTITY_CONTEXT_RULES}",
    ),
    "candidate_codes": PromptSpec(
        "candidate_codes",
        "v1_pos_guided_single_opinion_unit",
        CANDIDATE_CODE_SYSTEM_PROMPT,
    ),
    "candidate_normalization": PromptSpec(
        "candidate_normalization",
        "v4_group_first_compact_global_mapping",
        CANDIDATE_NORMALIZATION_SYSTEM_PROMPT,
    ),
    "comparative_validation": PromptSpec(
        "comparative_validation",
        "v2_implicit_shared_aspect_judger",
        COMPARATIVE_VALIDATION_SYSTEM_PROMPT,
    ),
    "overmerge_relabel": PromptSpec(
        "overmerge_relabel",
        "v1_domain_agnostic_relabel",
        RELABEL_SYSTEM_PROMPT,
    ),
}


def prompt_hashes() -> dict[str, str]:
    return {name: spec.sha256 for name, spec in PROMPTS.items()}
