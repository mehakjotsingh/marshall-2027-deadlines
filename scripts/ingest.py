"""Pick up the newest 12twenty export from ~/Downloads and stage it as data/details.json.

The browser does the fetching (bookmarklet, real Chrome, real session). This
just ingests. Exits 3 when there's no new export, so run.sh can stay quiet.
"""
import json, pathlib, sys, glob, os, shutil, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOWNLOADS = pathlib.Path.home() / "Downloads"


def newest_export():
    hits = glob.glob(str(DOWNLOADS / "12twenty-export*.json"))
    return max(hits, key=os.path.getmtime) if hits else None


def main():
    DATA.mkdir(exist_ok=True)
    src = newest_export()
    if not src:
        print("no export found in ~/Downloads", file=sys.stderr)
        return 3

    payload = json.loads(pathlib.Path(src).read_text())
    postings = payload.get("postings") or []
    if not postings:
        print("export contained no postings", file=sys.stderr)
        return 1

    stamp = (DATA / "last_export.txt")
    pulled = payload.get("pulled", "")
    if stamp.exists() and stamp.read_text().strip() == pulled:
        print(f"export already ingested ({pulled})", file=sys.stderr)
        return 3

    details = {str(p["Id"]): p for p in postings}
    (DATA / "details.json").write_text(json.dumps(details, indent=1))
    stamp.write_text(pulled)

    seen_path = DATA / "seen.json"
    seen = json.loads(seen_path.read_text()) if seen_path.exists() else {}
    new = [i for i in details if i not in seen]
    seen.update({i: True for i in details})
    seen_path.write_text(json.dumps(seen, indent=1))
    (DATA / "new_ids.json").write_text(json.dumps(new))

    archive = DATA / "exports"
    archive.mkdir(exist_ok=True)
    tag = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.move(src, archive / f"export-{tag}.json")

    print(f"ingested {len(details)} postings ({len(new)} new) from {os.path.basename(src)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
