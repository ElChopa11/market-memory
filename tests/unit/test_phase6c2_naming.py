"""Phase 6c-2 naming layer: single source, fail-closed unknown slugs."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mm_common.naming import (
    ARTIFACT_TYPES,
    PUBLISHING_DESKS,
    SLEEVE_MAP,
    UnknownNameError,
    as_config_dict,
    artifact_desk,
    artifact_display,
    coord_display,
    desk_display,
    require_artifact_type,
    require_publishing_desk,
    require_route_slug,
    sleeve_display,
    telegram_header,
)
from mm_desks.crypto import CryptoDesk
from mm_desks.equities import EquitiesDesk
from mm_desks.ic_risk import IcRiskDesk
from mm_desks.intel import IntelDesk
from mm_desks.ladder import LadderArtifact, artifact_to_envelope, make_artifact
from mm_desks.ops import OpsDesk
from mm_desks.orchestrator import PIPELINE, run_from_fixture
from mm_desks.quant import QuantDesk
from mm_desks.research import ResearchDesk
from mm_delivery.config import load_telegram_settings
from mm_delivery.fanout import fanout_desk
from mm_delivery.payload import build_payload
from mm_delivery.present import desk_header
from mm_common.time import parse_utc

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"
AS_OF = parse_utc("2026-09-18T00:00:00Z")


def test_yaml_matches_naming_module() -> None:
    raw = yaml.safe_load((ROOT / "config" / "desks" / "naming.yaml").read_text(encoding="utf-8"))
    assert raw == as_config_dict()


def test_publishing_desks_are_exactly_five() -> None:
    assert PUBLISHING_DESKS == ("intel", "research", "quant", "ic_risk", "ops")
    assert PIPELINE == PUBLISHING_DESKS
    assert desk_display("intel") == "Intel (Market Intelligence)"
    assert desk_display("research") == "Research (Investment Research)"
    assert desk_display("quant") == "Quant"
    assert desk_display("ic_risk") == "IC/Risk (Investment Committee & Risk)"
    assert desk_display("ops") == "Ops"
    assert coord_display() == "Coord (orchestration)"


def test_unknown_slug_fails_closed() -> None:
    for slug in ("crypto", "equities", "skeptic", "risk", "coord", "flow", "macro", "chart", "watchlist", "listings", "scorecard", "decay", "nope"):
        with pytest.raises(UnknownNameError, match=slug):
            require_publishing_desk(slug)
        with pytest.raises(UnknownNameError):
            desk_display(slug)
    with pytest.raises(UnknownNameError, match="coord"):
        require_route_slug("coord")
    with pytest.raises(UnknownNameError):
        require_artifact_type("SCAN_CARD")
    with pytest.raises(UnknownNameError):
        require_route_slug("crypto")


def test_sleeves_and_gates_are_labels_not_desks() -> None:
    assert SLEEVE_MAP["watchlist"] == "research"
    assert SLEEVE_MAP["listings"] == "research"
    assert SLEEVE_MAP["scorecard"] == "quant"
    assert SLEEVE_MAP["decay"] == "quant"
    assert "crypto" not in PUBLISHING_DESKS
    assert sleeve_display("watchlist").startswith("Research")
    assert sleeve_display("watchlist") == "Research (Investment Research) / watchlist monitor"
    with pytest.raises(UnknownNameError):
        require_publishing_desk("watchlist")
    with pytest.raises(UnknownNameError):
        require_publishing_desk("listings")
    with pytest.raises(UnknownNameError):
        require_publishing_desk("scorecard")
    with pytest.raises(UnknownNameError):
        require_publishing_desk("decay")
    assert sleeve_display("listings") == "Research (Investment Research) / listings IPO screen"
    assert sleeve_display("scorecard") == "Quant / like-for-like pack scorecard"
    assert sleeve_display("decay") == "Quant / prompt-hash decay watch"
    assert sleeve_display("crypto").startswith("Research")
    assert sleeve_display("equities").startswith("Research")
    assert sleeve_display("flow").startswith("Intel")
    assert sleeve_display("macro").startswith("Intel")
    assert sleeve_display("skeptic").startswith("IC/Risk")
    assert sleeve_display("risk").startswith("IC/Risk")
    with pytest.raises(UnknownNameError):
        sleeve_display("intel")


def test_artifact_types_have_human_labels_and_owning_desks() -> None:
    assert ARTIFACT_TYPES == (
        "DAILY_BIAS",
        "EDGE_SCAN",
        "INTEL_PACKET",
        "CHART_ARTIFACT",
        "OFFICIAL_BRIEF",
        "STATE_CARD",
    )
    assert artifact_display("DAILY_BIAS") == "Daily Bias"
    assert artifact_desk("DAILY_BIAS") == "research"
    assert artifact_desk("INTEL_PACKET") == "intel"
    assert artifact_desk("OFFICIAL_BRIEF") == "ops"
    assert artifact_desk("STATE_CARD") == "ops"
    assert artifact_desk("CHART_ARTIFACT") == "research"


def test_every_publishing_desk_class_resolves_through_naming() -> None:
    expected = {
        "intel": IntelDesk,
        "research": ResearchDesk,
        "quant": QuantDesk,
        "ic_risk": IcRiskDesk,
        "ops": OpsDesk,
    }
    for slug, cls in expected.items():
        desk = cls()
        assert desk.slug == slug
        assert desk.display_name == desk_display(slug)
        require_publishing_desk(desk.slug)


def test_sleeve_helpers_resolve_through_naming() -> None:
    crypto = CryptoDesk()
    equities = EquitiesDesk()
    assert crypto.display_name == sleeve_display("crypto")
    assert equities.display_name == sleeve_display("equities")
    with pytest.raises(UnknownNameError):
        require_publishing_desk(crypto.slug)


def test_pipeline_outputs_use_naming_display() -> None:
    result = run_from_fixture(FIXTURE, repo_root=ROOT)
    assert [row.slug for row in result.desks] == list(PIPELINE)
    for row in result.desks:
        assert row.desk == desk_display(row.slug)
        assert row.tier == require_publishing_desk(row.slug).tier


def test_retired_slug_rejected_by_orchestrator() -> None:
    with pytest.raises(UnknownNameError, match="crypto"):
        run_from_fixture(FIXTURE, repo_root=ROOT, slugs=("crypto",))


def test_telegram_payload_and_fanout_resolve_through_naming() -> None:
    settings = load_telegram_settings(ROOT)
    payload = build_payload("note", desk="research", as_of=AS_OF, settings=settings)
    assert payload.desk == "research"
    assert telegram_header("research") in desk_header("research")
    with pytest.raises(UnknownNameError):
        build_payload("note", desk="crypto", as_of=AS_OF, settings=settings)
    result = fanout_desk(
        "desk note BTC (observed)",
        desk="research",
        as_of=AS_OF,
        send=False,
        completeness_pct=100.0,
        repo=ROOT,
        settings=settings,
    )
    header = telegram_header("research")
    assert result.primary.payload.text.startswith(header)
    assert "desk note BTC (observed)" in result.primary.payload.text
    assert result.as_public_dict()["desk_display"] == desk_display("research")


def test_ladder_artifact_and_envelope_use_naming() -> None:
    art = make_artifact(
        artifact_type="DAILY_BIAS",
        run_id="r1",
        trade_math_hash="h",
        as_of=AS_OF,
        payload={
            "instrument": "BTC",
            "direction": "long",
            "conviction": "low",
            "level": "1",
            "trade_math_hash": "h",
        },
        threshold=0.0,
    )
    assert art.desk == "research"
    assert art.display_name == "Daily Bias"
    env = artifact_to_envelope(art)
    assert env.desk == "research"
    with pytest.raises(UnknownNameError):
        LadderArtifact(
            artifact_type="NOT_A_TYPE",
            run_id="r1",
            run_content_hash="",
            trade_math_hash="h",
            as_of_knowledge=AS_OF,
            payload={"trade_math_hash": "h"},
        )
