"""Localhost receiver so the bookmarklet can hand over data with no file dialog.

Binds 127.0.0.1 only and accepts POSTs solely from the 12twenty origin. Chrome's
Private Network Access rules require the preflight to carry
Access-Control-Allow-Private-Network, which is why OPTIONS is handled explicitly.
"""
import json, pathlib, subprocess, sys, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ORIGIN = "https://marshall-usc.12twenty.com"
PORT = 8787
MAX_BYTES = 32 * 1024 * 1024


class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_POST(self):
        if self.headers.get("Origin") != ORIGIN:
            self.send_response(403); self._cors(); self.end_headers(); return
        n = int(self.headers.get("Content-Length") or 0)
        if not 0 < n <= MAX_BYTES:
            self.send_response(413); self._cors(); self.end_headers(); return
        try:
            payload = json.loads(self.rfile.read(n))
            postings = payload.get("postings") or []
            if not postings:
                raise ValueError("no postings")
            # Sanity floor: never let a truncated or probe payload replace a
            # good dataset and silently publish an empty calendar.
            prev = DATA / "details.json"
            if prev.exists():
                n_prev = len(json.loads(prev.read_text()))
                if len(postings) < n_prev * 0.5:
                    raise ValueError(
                        f"refusing {len(postings)} postings; last good run had "
                        f"{n_prev}. Re-run the bookmarklet, or delete "
                        f"data/details.json to override.")
        except Exception as e:
            self.send_response(400); self._cors(); self.end_headers()
            self.wfile.write(str(e).encode()); return

        DATA.mkdir(exist_ok=True)
        (DATA / "exports").mkdir(exist_ok=True)
        tag = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        (DATA / "exports" / f"export-{tag}.json").write_text(json.dumps(payload))
        (DATA / "details.json").write_text(
            json.dumps({str(p["Id"]): p for p in postings}, indent=1))
        (DATA / "last_export.txt").write_text(payload.get("pulled", tag))

        subprocess.Popen([str(ROOT / "run.sh"), "--already-ingested"],
                         cwd=str(ROOT), start_new_session=True)
        self.send_response(200); self._cors()
        self.send_header("Content-Type", "text/plain"); self.end_headers()
        self.wfile.write(f"received {len(postings)}".encode())

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    try:
        HTTPServer(("127.0.0.1", PORT), H).serve_forever()
    except OSError as e:
        print(f"receiver: {e}", file=sys.stderr); sys.exit(1)
