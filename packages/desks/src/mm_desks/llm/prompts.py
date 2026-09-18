"""Versioned prompt files. Changing a prompt is a PR. Hash is recorded on every LLM row."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mm_common.hashing import sha256_hex

PROMPTS_REL = Path("config/prompts")
PROMPT_FILES = {
    "OFFICIAL_BRIEF": "official_brief.v1.txt",
    "EDGE_SCAN": "edge_scan.v1.txt",
    "SKEPTIC_REVIEW": "skeptic_review.v1.txt",
    "POST_MORTEM": "post_mortem.v1.txt",
}


@dataclass(frozen=True)
class PromptFile:
    artifact_type: str
    relpath: str
    text: str
    prompt_hash: str

    def canonical(self) -> dict[str, str]:
        return {
            "artifact_type": self.artifact_type,
            "prompt_file": self.relpath,
            "prompt_hash": self.prompt_hash,
        }


def load_prompt(artifact_type: str, repo_root: Path) -> PromptFile:
    name = PROMPT_FILES.get(artifact_type)
    if name is None:
        raise KeyError(f"no versioned prompt for {artifact_type}")
    relpath = str(PROMPTS_REL / name)
    path = Path(repo_root) / relpath
    text = path.read_text(encoding="utf-8")
    return PromptFile(
        artifact_type=artifact_type,
        relpath=relpath,
        text=text,
        prompt_hash=sha256_hex(text.encode("utf-8")),
    )
