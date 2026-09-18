"""Compat shim. Full prompt-hash decay watch lives in mm_quant.decay (IMP-031 / 6f).

6e recorded hashes with watch_enabled false. 6f turns the watch on.
"""

from mm_quant.decay import (
    ENGINE_VERSION as STUB_VERSION,
    ITEM,
    PHASE,
    WATCH_ENABLED,
    decay_watch_payload as decay_stub_payload,
    load_decay_config as load_decay_stub_config,
    prompt_hashes,
    repo_root,
)

__all__ = [
    "ITEM",
    "PHASE",
    "STUB_VERSION",
    "WATCH_ENABLED",
    "decay_stub_payload",
    "load_decay_stub_config",
    "prompt_hashes",
    "repo_root",
]
