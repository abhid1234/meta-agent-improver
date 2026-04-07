#!/usr/bin/env python3
"""
generate_charts.py — produce results/charts.html from meta-agent history.json.

Usage:
    python generate_charts.py [--history PATH] [--out PATH]

Defaults:
    --history  meta-agent/experience/ml-advisor/history.json
    --out      results/charts.html
"""

import argparse
import json
import math
import os
from pathlib import Path

SAMPLE_DATA = {
    "iterations": [
        {"name": "baseline", "reward": 0.8,  "pass_rate": 0.80, "n_passed": 24, "n_tasks": 30, "cost_usd": 1.89},
        {"name": "evo_001",  "reward": 0.83, "pass_rate": 0.83, "n_passed": 25, "n_tasks": 30, "cost_usd": 2.10},
        {"name": "evo_002",  "reward": 0.87, "pass_rate": 0.87, "n_passed": 26, "n_tasks": 30, "cost_usd": 1.95},
    ]
}

# ── palette ──────────────────────────────────────────────────────────────────
BG        = "#0d1117"
BG2       = "#161b22"
BG3       = "#21262d"
BORDER    = "#30363d"
TEXT      = "#e6edf3"
TEXT_MUTED= "#8b949e"
ACCENT    = "#00ff88"   # green = improvement
ACCENT2   = "#58a6ff"   # blue  = neutral series
WARN      = "#ff4444"   # red   = regression
GOLD      = "#ffd700"   # gold  = best

# ── SVG helpers ───────────────────────────────────────────────────────────────

def _fmt(v: float, decimals: int = 2) -> str:
    return f"{v:.{decimals}f}"


def line_chart(iterations: list[dict]) -> str:
    """Stepped line chart: pass_rate over iterations."""
    W, H = 760, 340
    PAD_L, PAD_R, PAD_T, PAD_B = 64, 24, 32, 56

    names     = [it["name"] for it in iterations]
    rates     = [it["pass_rate"] * 100 for it in iterations]
    baseline  = rates[0]
    n         = len(names)

    y_min = max(0,   math.floor(min(rates) / 10) * 10 - 10)
    y_max = min(100, math.ceil (max(rates) / 10) * 10 + 10)
    y_range = y_max - y_min or 1

    chart_w = W - PAD_L - PAD_R
    chart_h = H - PAD_T - PAD_B

    def cx(i):
        if n == 1:
            return PAD_L + chart_w / 2
        return PAD_L + i * chart_w / (n - 1)

    def cy(v):
        return PAD_T + chart_h - (v - y_min) / y_range * chart_h

    # y-grid & labels
    grid_lines = []
    y_ticks = range(y_min, y_max + 1, 10)
    for yv in y_ticks:
        yp = cy(yv)
        grid_lines.append(
            f'<line x1="{PAD_L}" y1="{_fmt(yp)}" x2="{W - PAD_R}" y2="{_fmt(yp)}" '
            f'stroke="{BORDER}" stroke-width="1"/>'
        )
        grid_lines.append(
            f'<text x="{PAD_L - 8}" y="{_fmt(yp + 4)}" text-anchor="end" '
            f'fill="{TEXT_MUTED}" font-size="11">{yv}%</text>'
        )

    # baseline dashed horizontal
    by = cy(baseline)
    baseline_line = (
        f'<line x1="{PAD_L}" y1="{_fmt(by)}" x2="{W - PAD_R}" y2="{_fmt(by)}" '
        f'stroke="{TEXT_MUTED}" stroke-width="1.5" stroke-dasharray="6,4"/>'
        f'<text x="{W - PAD_R + 2}" y="{_fmt(by + 4)}" fill="{TEXT_MUTED}" font-size="10">'
        f'baseline</text>'
    )

    # stepped polyline: horizontal then vertical
    pts = []
    for i, v in enumerate(rates):
        x, y = cx(i), cy(v)
        if i == 0:
            pts.append((x, y))
        else:
            prev_x = cx(i - 1)
            pts.append((x, pts[-1][1]))  # horizontal
            pts.append((x, y))           # vertical

    poly_points = " ".join(f"{_fmt(p[0])},{_fmt(p[1])}" for p in pts)

    # colored segments (green if up, red if down)
    segments = []
    for i in range(1, n):
        color = ACCENT if rates[i] >= rates[i - 1] else WARN
        sx, sy = cx(i - 1), cy(rates[i - 1])
        ex, ey = cx(i),     cy(rates[i])
        mid_x  = cx(i)
        segments.append(
            f'<polyline points="{_fmt(sx)},{_fmt(sy)} {_fmt(mid_x)},{_fmt(sy)} {_fmt(mid_x)},{_fmt(ey)}" '
            f'fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>'
        )

    # dots & x-labels
    dots = []
    xlabels = []
    for i, (name, v) in enumerate(zip(names, rates)):
        x, y = cx(i), cy(v)
        is_best = v == max(rates)
        color = GOLD if is_best else (ACCENT if i == 0 else ACCENT2)
        r = 6 if is_best else 4
        dots.append(
            f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{r}" '
            f'fill="{color}" stroke="{BG}" stroke-width="2">'
            f'<title>{name}: {_fmt(v)}%</title></circle>'
        )
        # value label above dot
        dots.append(
            f'<text x="{_fmt(x)}" y="{_fmt(y - 10)}" text-anchor="middle" '
            f'fill="{color}" font-size="11" font-weight="600">{_fmt(v)}%</text>'
        )
        # x-axis label (rotated for clarity)
        xlabels.append(
            f'<text transform="rotate(-35, {_fmt(x)}, {H - PAD_B + 14})" '
            f'x="{_fmt(x)}" y="{H - PAD_B + 14}" text-anchor="end" '
            f'fill="{TEXT_MUTED}" font-size="11">{name}</text>'
        )

    svg = f"""
<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;max-width:{W}px;display:block;margin:0 auto;">
  <rect width="{W}" height="{H}" fill="{BG2}" rx="10"/>
  {"".join(grid_lines)}
  {baseline_line}
  {"".join(segments)}
  {"".join(dots)}
  {"".join(xlabels)}
  <!-- axis lines -->
  <line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{H - PAD_B}"
        stroke="{BORDER}" stroke-width="1.5"/>
  <line x1="{PAD_L}" y1="{H - PAD_B}" x2="{W - PAD_R}" y2="{H - PAD_B}"
        stroke="{BORDER}" stroke-width="1.5"/>
</svg>"""
    return svg


def bar_chart(iterations: list[dict]) -> str:
    """Vertical bar chart: cost_usd per iteration."""
    W, H = 760, 300
    PAD_L, PAD_R, PAD_T, PAD_B = 64, 24, 32, 56

    names  = [it["name"]     for it in iterations]
    costs  = [it["cost_usd"] for it in iterations]
    n      = len(names)

    c_max  = max(costs) if costs else 1
    y_top  = math.ceil(c_max * 1.2 * 10) / 10  # 20 % headroom, 1 dp
    y_range= y_top or 1

    chart_w = W - PAD_L - PAD_R
    chart_h = H - PAD_T - PAD_B

    bar_gap  = 0.3
    bar_w    = chart_w / n * (1 - bar_gap)
    slot_w   = chart_w / n

    def bx(i):   return PAD_L + i * slot_w + slot_w * bar_gap / 2
    def by(v):   return PAD_T + chart_h - v / y_range * chart_h
    def bh(v):   return v / y_range * chart_h

    # y-grid
    grid_lines = []
    n_ticks = 5
    for k in range(n_ticks + 1):
        yv = y_top * k / n_ticks
        yp = by(yv)
        grid_lines.append(
            f'<line x1="{PAD_L}" y1="{_fmt(yp)}" x2="{W - PAD_R}" y2="{_fmt(yp)}" '
            f'stroke="{BORDER}" stroke-width="1"/>'
        )
        grid_lines.append(
            f'<text x="{PAD_L - 8}" y="{_fmt(yp + 4)}" text-anchor="end" '
            f'fill="{TEXT_MUTED}" font-size="11">${yv:.2f}</text>'
        )

    bars = []
    xlabels = []
    total_cost = sum(costs)
    for i, (name, cost) in enumerate(zip(names, costs)):
        x  = bx(i)
        y  = by(cost)
        bh_ = bh(cost)
        pct = cost / total_cost * 100 if total_cost else 0
        color = ACCENT2
        # gradient via two rects — lighter top
        bars.append(
            f'<rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(bar_w)}" height="{_fmt(bh_)}" '
            f'fill="{color}" rx="3" opacity="0.85">'
            f'<title>{name}: ${cost:.4f}</title></rect>'
        )
        # value label
        bars.append(
            f'<text x="{_fmt(x + bar_w / 2)}" y="{_fmt(y - 6)}" text-anchor="middle" '
            f'fill="{color}" font-size="11" font-weight="600">${cost:.2f}</text>'
        )
        # x-label
        cx_ = x + bar_w / 2
        xlabels.append(
            f'<text transform="rotate(-35, {_fmt(cx_)}, {H - PAD_B + 14})" '
            f'x="{_fmt(cx_)}" y="{H - PAD_B + 14}" text-anchor="end" '
            f'fill="{TEXT_MUTED}" font-size="11">{name}</text>'
        )

    svg = f"""
<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;max-width:{W}px;display:block;margin:0 auto;">
  <rect width="{W}" height="{H}" fill="{BG2}" rx="10"/>
  {"".join(grid_lines)}
  {"".join(bars)}
  {"".join(xlabels)}
  <line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{H - PAD_B}"
        stroke="{BORDER}" stroke-width="1.5"/>
  <line x1="{PAD_L}" y1="{H - PAD_B}" x2="{W - PAD_R}" y2="{H - PAD_B}"
        stroke="{BORDER}" stroke-width="1.5"/>
</svg>"""
    return svg


def summary_cards(iterations: list[dict]) -> str:
    baseline     = iterations[0]["pass_rate"] * 100
    best         = max(it["pass_rate"] for it in iterations) * 100
    improvement  = best - baseline
    total_cost   = sum(it["cost_usd"] for it in iterations)
    n_iters      = len(iterations) - 1  # excluding baseline

    imp_color = ACCENT if improvement >= 0 else WARN
    imp_sign  = "+" if improvement >= 0 else ""

    def card(label: str, value: str, sub: str = "", color: str = TEXT) -> str:
        return f"""
    <div style="background:{BG3};border:1px solid {BORDER};border-radius:10px;
                padding:20px 24px;flex:1;min-width:140px;">
      <div style="color:{TEXT_MUTED};font-size:12px;text-transform:uppercase;
                  letter-spacing:.08em;margin-bottom:8px;">{label}</div>
      <div style="color:{color};font-size:28px;font-weight:700;line-height:1;">{value}</div>
      {"" if not sub else f'<div style="color:{TEXT_MUTED};font-size:12px;margin-top:6px;">{sub}</div>'}
    </div>"""

    return f"""
<div style="display:flex;flex-wrap:wrap;gap:16px;margin-bottom:40px;">
  {card("Baseline Accuracy", f"{baseline:.1f}%", f"{iterations[0]['n_passed']}/{iterations[0]['n_tasks']} tasks")}
  {card("Best Accuracy", f"{best:.1f}%",
        f"{max(iterations, key=lambda x: x['pass_rate'])['n_passed']}/{iterations[0]['n_tasks']} tasks",
        color=GOLD)}
  {card("Improvement", f"{imp_sign}{improvement:.1f}pp", "vs baseline", color=imp_color)}
  {card("Total Cost", f"${total_cost:.2f}", f"{len(iterations)} run{'s' if len(iterations) != 1 else ''}")}
  {card("Evolution Rounds", str(n_iters), "after baseline")}
</div>"""


def build_html(iterations: list[dict], benchmark: str = "ml-advisor") -> str:
    acc_svg   = line_chart(iterations)
    cost_svg  = bar_chart(iterations)
    cards_html= summary_cards(iterations)

    best_iter  = max(iterations, key=lambda x: x["pass_rate"])
    best_name  = best_iter["name"]
    best_rate  = best_iter["pass_rate"] * 100
    baseline_r = iterations[0]["pass_rate"] * 100
    delta      = best_rate - baseline_r
    delta_str  = f"+{delta:.1f}pp" if delta >= 0 else f"{delta:.1f}pp"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Meta-Agent Results — {benchmark}</title>
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{
    background:{BG};
    color:{TEXT};
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
    line-height:1.6;
    padding:40px 24px;
  }}
  .container{{max-width:860px;margin:0 auto;}}
  .header{{margin-bottom:40px;}}
  .header h1{{
    font-size:28px;font-weight:700;
    background:linear-gradient(90deg,{ACCENT},{ACCENT2});
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    background-clip:text;
    margin-bottom:8px;
  }}
  .header p{{color:{TEXT_MUTED};font-size:14px;}}
  .badge{{
    display:inline-block;padding:3px 10px;border-radius:20px;
    font-size:12px;font-weight:600;margin-left:10px;vertical-align:middle;
    background:{ACCENT}22;color:{ACCENT};border:1px solid {ACCENT}44;
  }}
  .section{{margin-bottom:48px;}}
  .section-title{{
    font-size:14px;font-weight:600;text-transform:uppercase;
    letter-spacing:.1em;color:{TEXT_MUTED};margin-bottom:16px;
    padding-bottom:8px;border-bottom:1px solid {BORDER};
  }}
  .chart-wrap{{
    border-radius:10px;overflow:hidden;
    border:1px solid {BORDER};
  }}
  .footer{{
    margin-top:48px;padding-top:24px;border-top:1px solid {BORDER};
    color:{TEXT_MUTED};font-size:12px;text-align:center;
  }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>Meta-Agent Benchmark Results
      <span class="badge">{benchmark}</span>
    </h1>
    <p>Evolutionary prompt optimisation · best run: <strong style="color:{GOLD}">{best_name}</strong>
       ({best_rate:.1f}% accuracy, <span style="color:{'#00ff88' if delta >= 0 else '#ff4444'}">{delta_str}</span> vs baseline)</p>
  </div>

  <div class="section">
    <div class="section-title">Summary</div>
    {cards_html}
  </div>

  <div class="section">
    <div class="section-title">Accuracy over Iterations</div>
    <div class="chart-wrap">
      {acc_svg}
    </div>
  </div>

  <div class="section">
    <div class="section-title">Cost per Iteration (USD)</div>
    <div class="chart-wrap">
      {cost_svg}
    </div>
  </div>

  <div class="footer">
    Generated by generate_charts.py &mdash; data from {benchmark}/history.json
  </div>

</div>
</body>
</html>"""


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    here = Path(__file__).parent

    parser = argparse.ArgumentParser(description="Generate benchmark charts HTML")
    parser.add_argument(
        "--history",
        default=str(here / "meta-agent/experience/ml-advisor/history.json"),
        help="Path to history.json",
    )
    parser.add_argument(
        "--out",
        default=str(here / "results/charts.html"),
        help="Output HTML path",
    )
    args = parser.parse_args()

    history_path = Path(args.history)
    out_path     = Path(args.out)

    if history_path.exists():
        with open(history_path) as f:
            data = json.load(f)
        print(f"Loaded {len(data['iterations'])} iteration(s) from {history_path}")
    else:
        print(f"history.json not found at {history_path}, using sample data.")
        data = SAMPLE_DATA

    iterations = data["iterations"]
    benchmark  = data.get("benchmark", history_path.parent.name)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = build_html(iterations, benchmark)

    with open(out_path, "w") as f:
        f.write(html)

    print(f"Charts written to {out_path}")


if __name__ == "__main__":
    main()
