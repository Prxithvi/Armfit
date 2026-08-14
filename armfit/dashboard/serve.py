"""Tiny local dashboard: just serves the generated report directory."""
import functools
import http.server
import webbrowser
from pathlib import Path


def launch(out_dir: Path, port: int = 8765, open_browser: bool = True) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out_dir))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/armfit-report.html"
    print(f"\nArmFit dashboard running at {url}")
    print("Press Ctrl+C to stop.\n")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ArmFit dashboard.")
        httpd.shutdown()
