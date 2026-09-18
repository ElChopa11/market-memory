"""Concentration clusters from versioned trailing-corr config — not hand-named in code."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from mm_quant.mathutil import pearson

CLUSTERS_REL = Path("config/risk/clusters.yaml")


@dataclass(frozen=True)
class ClusterConfig:
    version: str
    window: int
    min_overlap: int
    corr_threshold: float
    max_cluster_pct: float
    rule_id: str
    clusters: dict[str, tuple[str, tuple[str, ...]]]  # id -> (seed, candidates)


def load_cluster_config(repo_root: Path) -> ClusterConfig:
    path = Path(repo_root) / CLUSTERS_REL
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
    if not isinstance(data, dict):
        data = {}
    clusters: dict[str, tuple[str, tuple[str, ...]]] = {}
    raw = data.get("clusters") if isinstance(data.get("clusters"), dict) else {}
    for cid, spec in raw.items():
        if not isinstance(spec, dict):
            continue
        seed = str(spec.get("seed") or "").upper()
        cands = tuple(str(x).upper() for x in (spec.get("candidates") or []))
        clusters[str(cid)] = (seed, cands)
    return ClusterConfig(
        version=str(data.get("version") or "imp-016.1"),
        window=int(data.get("window") or 60),
        min_overlap=int(data.get("min_overlap") or 20),
        corr_threshold=float(data.get("corr_threshold") or 0.65),
        max_cluster_pct=float(data.get("max_cluster_pct") or 50),
        rule_id=str(data.get("rule_id") or "cluster_concentration"),
        clusters=clusters,
    )


def _returns(prices: Sequence[float]) -> list[float]:
    out: list[float] = []
    for i in range(1, len(prices)):
        if prices[i - 1] == 0:
            continue
        out.append(prices[i] / prices[i - 1] - 1.0)
    return out


def cluster_membership(
    prices_by_instrument: Mapping[str, Sequence[float]],
    config: ClusterConfig,
) -> dict[str, tuple[str, ...]]:
    """Assign instruments to clusters when trailing corr vs seed >= threshold."""
    members: dict[str, list[str]] = {cid: [] for cid in config.clusters}
    window = config.window
    for cid, (seed, candidates) in config.clusters.items():
        seed_px = list(prices_by_instrument.get(seed) or [])
        seed_r = _returns(seed_px)[-window:]
        for name in candidates:
            series = list(prices_by_instrument.get(name) or [])
            ret = _returns(series)[-window:]
            n = min(len(seed_r), len(ret))
            if n < config.min_overlap:
                if name == seed:
                    members[cid].append(name)
                continue
            corr = pearson(seed_r[-n:], ret[-n:])
            if name == seed or (corr is not None and corr >= config.corr_threshold):
                members[cid].append(name)
    return {cid: tuple(sorted(set(names))) for cid, names in members.items()}


def cluster_of(instrument: str, membership: Mapping[str, tuple[str, ...]]) -> str | None:
    inst = instrument.upper()
    hits = [cid for cid, names in membership.items() if inst in names]
    return hits[0] if hits else None
