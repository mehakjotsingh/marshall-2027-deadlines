"""Emit docs/deadlines.ics and docs/index.html from classified postings."""
import json, pathlib, datetime, html
import config

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS, DATA = ROOT / "docs", ROOT / "data"
PACIFIC = datetime.timezone(datetime.timedelta(hours=-7))  # deadlines are stored 06:59Z = 23:59 PT


def esc(s):
    return (s.replace("\\", "\\\\").replace(";", r"\;")
             .replace(",", r"\,").replace("\n", r"\n"))


def fold(line):
    """RFC 5545 line folding at <=75 octets.

    Must never split a multi-byte character across a fold, so we measure each
    CHARACTER's encoded width instead of slicing raw bytes.
    """
    out, cur, width = [], "", 0
    for ch in line:
        w = len(ch.encode("utf-8"))
        if width + w > 73:
            out.append(cur)
            cur, width = " ", 1
        cur += ch
        width += w
    out.append(cur)
    return "\r\n".join(out)


def deadline_pt(iso):
    """12twenty stores deadlines in UTC; 06:59Z is 23:59 the prior day in PT."""
    if not iso:
        return None
    dt = datetime.datetime.fromisoformat(iso).replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(PACIFIC)


def opened_date(iso):
    """Opening dates are date-only (T00:00:00) and must NOT be shifted from UTC,
    unlike deadlines which are real UTC timestamps (06:59Z = 23:59 PT prior day).
    PostedDate does carry a real time, so that one is converted."""
    if not iso:
        return None
    dt = datetime.datetime.fromisoformat(iso)
    if (dt.hour, dt.minute, dt.second) == (0, 0, 0):
        return dt                                    # already a local calendar date
    return dt.replace(tzinfo=datetime.timezone.utc).astimezone(PACIFIC)


def build_ics(rows):
    rows = [r for r in rows if r.get('tier', 'firm') == 'firm']
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    L = ["BEGIN:VCALENDAR", "VERSION:2.0",
         "PRODID:-//USC Marshall Class of 2027//Recruiting Deadlines//EN",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         "X-WR-CALNAME:Marshall 2027 Recruiting Deadlines",
         "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
         "X-PUBLISHED-TTL:PT12H"]
    for r in rows:
        d = deadline_pt(r["deadline"])
        if not d:
            continue
        start = d.strftime("%Y%m%d")
        end = (d + datetime.timedelta(days=1)).strftime("%Y%m%d")
        url = config.JOB_URL.format(id=r["id"])
        op = opened_date(r.get("opened"))
        opened_line = f"\\nOpened: {op.strftime('%a %b %d, %Y')}" if op else ""
        desc = (f"{esc(r['title'])}\\n\\nDeadline: 11:59 PM PT on {d.strftime('%a %b %d, %Y')}"
                f"{opened_line}"
                f"\\n{esc(r['auth_note'])}\\n{esc(r['why'])}\\n\\n12twenty (Marshall login required):\\n{url}")
        L += ["BEGIN:VEVENT", f"UID:marshall2027-{r['id']}@12twenty.local",
              f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{start}", f"DTEND;VALUE=DATE:{end}",
              fold(f"SUMMARY:DUE: {esc(r['employer'])} - {esc(r['title'])}"),
              fold(f"DESCRIPTION:{desc}"), fold(f"URL:{url}"),
              "TRANSP:TRANSPARENT", "STATUS:CONFIRMED", "SEQUENCE:0",
              "BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:-P2D",
              fold(f"DESCRIPTION:2 days until {esc(r['employer'])} deadline"),
              "END:VALARM", "END:VEVENT"]
    L.append("END:VCALENDAR")
    return "\r\n".join(L) + "\r\n"


def _rows_html(rows):
    trs = []
    for r in sorted(rows, key=lambda x: x["deadline"] or ""):
        d = deadline_pt(r["deadline"])
        op = opened_date(r.get("opened"))
        trs.append(
            f"<tr><td class=d>{d.strftime('%a %b %-d') if d else '--'}</td>"
            f"<td class=o>{op.strftime('%b %-d') if op else '--'}</td>"
            f"<td><strong>{html.escape(r['employer'])}</strong><br>"
            f"<a href='{html.escape(config.JOB_URL.format(id=r['id']))}'>"
            f"{html.escape(r['title'])}</a></td>"
            f"<td class=n>{html.escape(r['why'])}</td></tr>")
    return ("<table><tr><th>Due</th><th>Opened</th><th>Role</th><th></th></tr>"
            + "".join(trs) + "</table>")


def build_html(rows, updated):
    firm = [r for r in rows if r.get("tier", "firm") == "firm"]
    maybe = [r for r in rows if r.get("tier") == "maybe"]
    maybe_block = ""
    if maybe:
        maybe_block = (f"<h2>Worth a look &middot; {len(maybe)}</h2>"
                       "<p class=sub2>Open to sponsorship and not senior, but they never state a "
                       "graduation year &mdash; often just a vague job description rather than a role "
                       "that excludes you. Not in the calendar feed; skim these yourself.</p>"
                       + _rows_html(maybe))
    return f"""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Marshall 2027 Recruiting Deadlines</title>
<style>
:root{{color-scheme:light dark;--bg:#fff;--fg:#16181d;--mut:#5b6472;--line:#e3e6ea;--acc:#990000}}
@media(prefers-color-scheme:dark){{:root{{--bg:#14161a;--fg:#e8eaed;--mut:#9aa4b2;--line:#2a2e35;--acc:#ff6b6b}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,system-ui,sans-serif;
max-width:900px;margin:0 auto;padding-block:32px;padding-left:20px;padding-right:20px}}
h1{{font-size:22px;margin:0 0 4px}}
h2{{font-size:17px;margin:38px 0 4px;padding-top:22px;border-top:1px solid var(--line)}}
p.sub,p.sub2{{color:var(--mut);margin:0 0 20px;font-size:14px}}
a.sub-btn{{display:inline-block;background:var(--acc);color:#fff;padding:10px 18px;border-radius:7px;
text-decoration:none;font-weight:600;margin-bottom:14px}}
p.alt{{color:var(--mut);font-size:13px;margin:0 0 22px}}
code.url{{display:inline-block;background:#8881;padding:7px 10px;border-radius:5px;font-size:12px;
word-break:break-all;margin-top:6px;user-select:all}}
table{{border-collapse:collapse;width:100%}}
td{{padding:11px 8px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);
padding:0 8px 8px;border-bottom:1px solid var(--line)}}
td.d{{white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--mut);width:90px}}
td.o{{white-space:nowrap;color:var(--mut);font-size:13px;width:70px}}
td.n{{color:var(--mut);font-size:13px}}
a{{color:var(--acc)}} footer{{color:var(--mut);font-size:13px;margin-top:30px}}
@media(max-width:560px){{td.o,th:nth-child(2){{display:none}}}}
</style>
<h1>Marshall 2027 Recruiting Deadlines</h1>
<p class=sub>On-cycle full-time roles for the Class of 2027 that accept sponsorship.
All deadlines 11:59&nbsp;PM&nbsp;PT.</p>
<a class=sub-btn href="webcal://mehakjotsingh.github.io/marshall-2027-deadlines/deadlines.ics">Subscribe in Calendar</a>
<p class=alt>Button not working? Copy this URL and add it manually &mdash;
Apple Calendar: <em>File &rsaquo; New Calendar Subscription</em>.
Google Calendar: <em>Other calendars &rsaquo; From URL</em>.<br>
<code class=url>https://mehakjotsingh.github.io/marshall-2027-deadlines/deadlines.ics</code></p>
<h2>Firm &middot; {len(firm)}</h2>
<p class=sub2>These state a 2027 graduation or start requirement. This is what the calendar feed contains.</p>
{_rows_html(firm)}
{maybe_block}
<footer>{len(firm)} firm &middot; {len(maybe)} worth a look &middot; updated {updated}
&middot; postings require a Marshall 12twenty login</footer>"""


def main():
    rows = json.loads((DATA / "classified.json").read_text())
    DOCS.mkdir(exist_ok=True)
    firm = [r for r in rows if r.get("tier", "firm") == "firm"]
    (DOCS / "deadlines.ics").write_text(build_ics(rows), newline="")
    updated = datetime.datetime.now(PACIFIC).strftime("%b %-d, %Y")
    (DOCS / "index.html").write_text(build_html(rows, updated))
    print(f"built {len(firm)} calendar events ({len(rows) - len(firm)} more on the page) "
          f"-> docs/deadlines.ics, docs/index.html")


if __name__ == "__main__":
    main()
