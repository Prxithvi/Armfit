from string import Template

# Uses $-style placeholders (string.Template) instead of str.format/f-strings
# because the CSS below is full of literal { } braces.
HTML_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ArmFit Report — $model_name</title>
<style>
  :root {
    --bg: #08090d;
    --bg-glow: radial-gradient(1200px 600px at 15% -10%, rgba(255,106,61,0.10), transparent),
               radial-gradient(900px 500px at 100% 0%, rgba(61,220,151,0.08), transparent);
    --panel: #12141b;
    --panel2: #191c26;
    --border: #24283a;
    --border-soft: #1b1e2a;
    --text: #eef0f6;
    --muted: #8b93a7;
    --muted-dim: #5c6274;
    --accent: #ff6a3d;
    --accent-soft: #ff8a5e;
    --accent2: #3ddc97;
    --warn: #f5c451;
    --danger: #ff5470;
    --radius-lg: 16px;
    --radius-md: 12px;
    --radius-sm: 8px;
  }
  * { box-sizing: border-box; }
  html { -webkit-font-smoothing: antialiased; }
  body {
    margin: 0; padding: 48px 24px 90px;
    background-color: var(--bg);
    background-image: var(--bg-glow);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
    font-feature-settings: "tnum" 1, "cv11" 1;
  }
  .wrap { max-width: 960px; margin: 0 auto; }

  .hero {
    display: flex; align-items: flex-start; justify-content: space-between;
    flex-wrap: wrap; gap: 16px; margin-bottom: 32px;
  }
  .hero-left h1 {
    font-size: 30px; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 6px;
  }
  .hero-left .sub { color: var(--muted); margin: 0; font-size: 14px; }
  .hero-left .sub b { color: var(--text); font-weight: 600; }

  .badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px 5px 10px; border-radius: 999px;
    font-size: 12px; font-weight: 700; letter-spacing: 0.01em;
    border: 1px solid transparent;
  }
  .badge .dot { width: 6px; height: 6px; border-radius: 50%; }
  .badge.measured { background: rgba(61,220,151,0.12); color: var(--accent2); border-color: rgba(61,220,151,0.25); }
  .badge.measured .dot { background: var(--accent2); box-shadow: 0 0 8px rgba(61,220,151,0.8); }
  .badge.projected { background: rgba(245,196,81,0.12); color: var(--warn); border-color: rgba(245,196,81,0.25); }
  .badge.projected .dot { background: var(--warn); box-shadow: 0 0 8px rgba(245,196,81,0.8); }

  .cards { display: grid; grid-template-columns: 1fr 1fr 1.15fr; gap: 16px; margin-bottom: 24px; }
  .card {
    position: relative; overflow: hidden;
    background: linear-gradient(160deg, var(--panel), var(--panel2));
    border: 1px solid var(--border); border-radius: var(--radius-lg);
    padding: 20px 20px 18px;
    transition: border-color .15s ease, transform .15s ease;
  }
  .card:hover { border-color: #33394c; transform: translateY(-1px); }
  .card .label {
    color: var(--muted); font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .06em; display: flex; align-items: center; gap: 6px;
  }
  .card .value { font-size: 30px; font-weight: 800; margin-top: 10px; letter-spacing: -0.01em; }
  .card .value .unit { font-size: 15px; color: var(--muted); font-weight: 600; margin-left: 3px; }
  .card .value.accent {
    background: linear-gradient(90deg, var(--accent2), #67e8c2);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }

  .gauge-card { display: flex; align-items: center; gap: 16px; }
  .gauge {
    --pct: 0;
    width: 74px; height: 74px; border-radius: 50%; flex-shrink: 0;
    background: conic-gradient(var(--accent2) calc(var(--pct) * 1%), var(--border-soft) 0);
    display: flex; align-items: center; justify-content: center;
    position: relative;
  }
  .gauge::before {
    content: ""; position: absolute; inset: 7px; border-radius: 50%; background: var(--panel);
  }
  .gauge span {
    position: relative; font-size: 15px; font-weight: 800; color: var(--accent2);
  }
  .gauge-text .value { margin-top: 4px; }
  .gauge-text .hint { font-size: 12px; color: var(--muted-dim); margin-top: 2px; }

  section {
    background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius-lg);
    padding: 24px; margin-bottom: 18px;
  }
  section h2 {
    margin: 0 0 18px; font-size: 13px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; color: var(--muted); display: flex; align-items: center; gap: 8px;
  }
  section h2::before {
    content: ""; width: 3px; height: 14px; border-radius: 2px;
    background: linear-gradient(180deg, var(--accent), var(--accent2));
  }

  .bn-row { display: flex; align-items: center; gap: 14px; padding: 11px 0; border-bottom: 1px solid var(--border-soft); }
  .bn-row:last-child { border-bottom: none; }
  .bn-rank {
    width: 24px; height: 24px; border-radius: 7px; background: var(--panel2);
    color: var(--muted); font-weight: 700; font-size: 12px;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .bn-name { width: 130px; font-weight: 600; font-size: 14px; flex-shrink: 0; }
  .bn-bar-track { flex: 1; background: var(--panel2); border-radius: 6px; overflow: hidden; height: 16px; }
  .bn-bar-fill {
    height: 100%; border-radius: 6px;
    background: linear-gradient(90deg, var(--accent), var(--accent-soft));
    box-shadow: 0 0 12px rgba(255,106,61,0.35);
  }
  .bn-pct { width: 56px; text-align: right; font-variant-numeric: tabular-nums; color: var(--muted); font-size: 13px; }
  .bn-impact {
    width: 96px; text-align: right; font-size: 11px; font-weight: 800;
    text-transform: uppercase; letter-spacing: .03em;
  }
  .impact-very-high, .impact-high { color: var(--danger); }
  .impact-medium { color: var(--warn); }
  .impact-low { color: var(--muted-dim); }

  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th, td { text-align: right; padding: 10px 8px; border-bottom: 1px solid var(--border-soft); }
  th:first-child, td:first-child { text-align: left; }
  th { color: var(--muted); font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: .04em; }
  tr:last-child td { border-bottom: none; }
  td.pos { color: var(--warn); font-weight: 600; }
  td.neg { color: var(--accent2); font-weight: 600; }

  .insights { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
  .insights li {
    padding: 14px 16px; background: var(--panel2);
    border-left: 3px solid var(--accent2); border-radius: var(--radius-sm);
    font-size: 14px; line-height: 1.55;
  }
  .insights li.note { border-left-color: var(--warn); color: var(--muted); font-size: 13px; }

  footer {
    text-align: center; color: var(--muted-dim); font-size: 12px;
    margin-top: 36px; padding-top: 20px; border-top: 1px solid var(--border-soft);
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <div class="hero-left">
      <h1>ArmFit Performance Report</h1>
      <p class="sub">Model: <b>$model_name</b> &nbsp;·&nbsp; Generated $timestamp &nbsp;·&nbsp; Mode: <b>$mode</b></p>
    </div>
    <span class="badge $measured_class"><span class="dot"></span>$measured_text</span>
  </div>

  <div class="cards">
    <div class="card">
      <div class="label">Baseline (SME2 OFF)</div>
      <div class="value">$baseline_ms<span class="unit">ms</span></div>
    </div>
    <div class="card">
      <div class="label">SME2 ON</div>
      <div class="value accent">$sme2_ms<span class="unit">ms</span></div>
    </div>
    <div class="card gauge-card">
      <div class="gauge" style="--pct:$speedup_pct"><span>$speedup_pct%</span></div>
      <div class="gauge-text">
        <div class="label">Improvement</div>
        <div class="value accent" style="font-size:20px;">Faster</div>
        <div class="hint">$baseline_ms ms &rarr; $sme2_ms ms</div>
      </div>
    </div>
  </div>

  <section>
    <h2>Top Bottlenecks (baseline)</h2>
    $bottleneck_rows
  </section>

  <section>
    <h2>SME2 OFF vs ON — Category Comparison</h2>
    <table>
      <tr><th>Category</th><th>OFF (ms)</th><th>ON (ms)</th><th>&Delta; ms</th><th>&Delta; %</th></tr>
      $comparison_rows
    </table>
  </section>

  <section>
    <h2>What This Means</h2>
    <ul class="insights">
      $insight_items
    </ul>
  </section>

  <footer>ArmFit — from profiler data to performance decisions.</footer>
</div>
</body>
</html>
""")
