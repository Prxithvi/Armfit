import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from armfit.report.template import HTML_TEMPLATE


def build_report_data(model_path: str, mode: str, baseline, sme2, ranked, comparison, insights) -> Dict:
    return {
        "model": model_path,
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "measured": comparison["measured"],
        "baseline": {
            "label": baseline.label,
            "total_time_ms": baseline.total_time_ms,
            "categories": [c.__dict__ for c in baseline.categories],
        },
        "sme2": {
            "label": sme2.label,
            "total_time_ms": sme2.total_time_ms,
            "categories": [c.__dict__ for c in sme2.categories],
        },
        "bottlenecks": ranked,
        "comparison": comparison,
        "insights": insights,
    }


def export_json(report_data: Dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "armfit-report.json"
    path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    return path


def _bottleneck_rows_html(ranked) -> str:
    rows = []
    for b in ranked:
        # kebab-case, not dot-separated: a dot inside a CSS class attribute
        # value is fine, but ".impact-Very.High" as a *selector* means two
        # chained classes ("impact-Very" AND "High"), so it silently never
        # matched. "very-high" + a matching ".impact-very-high" selector
        # in the stylesheet fixes that.
        impact_class = "impact-" + b["impact"].lower().replace(" ", "-")
        rows.append(f"""
        <div class="bn-row">
          <div class="bn-rank">#{b['rank']}</div>
          <div class="bn-name">{b['category']}</div>
          <div class="bn-bar-track"><div class="bn-bar-fill" style="width:{min(b['pct'],100)}%"></div></div>
          <div class="bn-pct">{b['pct']}%</div>
          <div class="bn-impact {impact_class}">{b['impact']}</div>
        </div>""")
    return "".join(rows)


def _comparison_rows_html(comparison) -> str:
    rows = []
    for r in comparison["rows"]:
        cls = "pos" if r["delta_ms"] > 0 else ("neg" if r["delta_ms"] < 0 else "")
        sign = "+" if r["delta_ms"] > 0 else ""
        rows.append(
            f"<tr><td>{r['category']}</td><td>{r['off_ms']}</td><td>{r['on_ms']}</td>"
            f"<td class=\"{cls}\">{sign}{r['delta_ms']}</td><td class=\"{cls}\">{sign}{r['delta_pct']}%</td></tr>"
        )
    return "".join(rows)


def _insight_items_html(insights) -> str:
    items = []
    for text in insights:
        is_note = text.startswith("Note:")
        cls = ' class="note"' if is_note else ""
        items.append(f"<li{cls}>{text}</li>")
    return "".join(items)


def export_html(report_data: Dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "armfit-report.html"

    measured = report_data["measured"]
    html = HTML_TEMPLATE.substitute(
        model_name=Path(report_data["model"]).name,
        timestamp=report_data["generated_at"][:19].replace("T", " ") + " UTC",
        mode=report_data["mode"],
        measured_class="measured" if measured else "projected",
        measured_text="MEASURED (real Arm hardware)" if measured else "PROJECTED (dev-mode estimate)",
        baseline_ms=report_data["baseline"]["total_time_ms"],
        sme2_ms=report_data["sme2"]["total_time_ms"],
        speedup_pct=report_data["comparison"]["overall_speedup_pct"],
        bottleneck_rows=_bottleneck_rows_html(report_data["bottlenecks"]),
        comparison_rows=_comparison_rows_html(report_data["comparison"]),
        insight_items=_insight_items_html(report_data["insights"]),
    )
    path.write_text(html)
    return path
