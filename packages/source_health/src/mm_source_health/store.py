"""Write versioned source-health markdown under ops/reports/source-health/."""

from __future__ import annotations

from pathlib import Path

from mm_source_health.models import HealthReport


def artifact_relpath(report: HealthReport) -> Path:
    day = report.generated_at.date().isoformat()
    return Path("ops") / "reports" / "source-health" / f"{day}.md"


def write_source_health_report(report: HealthReport, *, root: Path) -> Path:
    rel = artifact_relpath(report)
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.markdown, encoding="utf-8")
    path.with_suffix(".sha256").write_text(report.content_hash + "\n", encoding="utf-8")
    return path
