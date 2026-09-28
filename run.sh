#!/bin/bash
# Ingest the newest 12twenty export -> classify -> build -> publish.
#
# The scrape itself is NOT automated. 12twenty sits behind USC SSO + Duo and
# Cloudflare bot detection; headless browsers are challenged, and Chrome 136+
# refuses remote debugging on the default profile. So the data pull is one
# bookmarklet click in real Chrome, and everything after it is automatic.
cd "$(dirname "$0")" || exit 1
PY=./.venv/bin/python
[ -x "$PY" ] || PY=python3
exec >> data/run.log 2>&1
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="

notify() { osascript -e "display notification \"$2\" with title \"$1\""; }

if [ "$1" = "--already-ingested" ]; then
  rc=0                      # receiver.py staged data/details.json for us
else
  $PY scripts/ingest.py
  rc=$?
fi
[ $rc -eq 3 ] && { echo "nothing new"; exit 0; }
[ $rc -ne 0 ] && { notify "Marshall 2027" "Ingest failed - see data/run.log"; exit $rc; }

before=$(md5 -q docs/deadlines.ics 2>/dev/null || echo none)
$PY scripts/classify.py || { notify "Marshall 2027" "Classify failed"; exit 1; }
$PY scripts/build.py    || { notify "Marshall 2027" "Build failed"; exit 1; }
after=$(md5 -q docs/deadlines.ics)

n=$($PY -c "import json;print(len(json.load(open('data/classified.json'))))")
if [ "$before" != "$after" ]; then
  git add -A docs data/seen.json data/last_export.txt
  git commit -q -m "Refresh deadlines: $n roles ($(date '+%Y-%m-%d'))" || true
  if git push -q 2>/dev/null; then
    notify "Marshall 2027" "$n roles published"
  else
    notify "Marshall 2027" "Built $n roles - push failed, run: git push"
  fi
else
  notify "Marshall 2027" "No change ($n roles)"
fi
