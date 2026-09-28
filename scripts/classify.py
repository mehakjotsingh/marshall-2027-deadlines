"""Rule-based screen: on-cycle Class-of-2027 full-time roles open to sponsorship.

No LLM. Two independent gates, both derived from real 12twenty data:

  1. Work authorization. 12twenty exposes the requirement twice -- a scalar
     (RequiredWorkAuthName) and a list (WorkAuthRequirements). We take the union
     and apply the stricter reading: keep a posting only if "All Work
     Authorizations Accepted" is present AND "Permanent US Work Authorization
     Required" is absent from either field.

  2. Cycle. Employer metadata (JobPostingJobTypeNames, the feed in ContactName)
     is unreliable -- Gartner tags a full-time 2027 graduate role as an
     "Internship" -- so metadata kills are overridable by an explicit
     graduate-year phrase in the title. Internship wording in the title or
     body is never overridable.
"""
import re

ALL_OK = "All Work Authorizations Accepted"
PERM = "Permanent US Work Authorization Required"
STEM = "STEM Eligible Degree"

I = re.IGNORECASE
TITLE_KILL = [re.compile(p, I) for p in (
    r"\bintern(?:ship)?s?\b", r"\bsummer\s+(?:associate|analyst)\b", r"\bco-?op\b")]
BODY_KILL = [re.compile(p, I) for p in (
    r"(?:summer|spring|fall|winter)\s*20(?:27|28)\b[^.]{0,70}\bintern",
    r"\bintern(?:ship)?\b[^.]{0,70}(?:summer|spring|fall|winter)\s*20(?:27|28)",
    r"graduat\w{0,12}[^.]{0,55}\b2028\b",
    r"\b2028\b[^.]{0,55}graduat",
    r"enrolled[^.]{0,70}(?:fall|spring|during)\s*2027",
    r"\b2027\b[^.]{0,45}\bsemester\b")]
TITLE_RESCUE = [re.compile(p, I) for p in (
    r"\b20\d\d\s+graduates?\b", r"class of 20\d\d",
    r"\buniversity graduate\b", r"\bgraduate program\b")]
TITLE_POS = [re.compile(p) for p in (
    r"\b2027\b", r"\b20\d\d\s*/\s*2027\b", r"\b2027\s*/\s*20\d\d\b")]
BODY_POS = [re.compile(p, I) for p in (
    r"class of 2027",
    r"graduat\w{0,12}[^.]{0,75}\b2027\b",
    r"\b2027\b[^.]{0,55}graduat",
    r"\b(?:start|begin|commenc|join)\w{0,8}[^.]{0,65}\b2027\b",
    r"\b2027\b[^.]{0,45}\b(?:start|cohort|hire|class)\b",
    r"\bfull[- ]time[^.]{0,65}\b2027\b",
    r"\b(?:degree|qualification|completion|diploma)\b[^.]{0,85}\b2027\b")]

SENIOR = re.compile(
    r"\b(senior|sr\.?|director|principal|vp|vice president|head of|chief|executive)\b", I)
YEARS = re.compile(r"(\d+)\s*\+?\s*(?:-\s*\d+\s*)?years?[^.]{0,40}experience", I)
MAX_YEARS_FOR_MAYBE = 5
# "...solving infrastructure challenges for more than 85 years with a legacy of
# expertise, experience" parses as an 85-year requirement. Anything above this is
# company age or boilerplate, not a hiring bar.
MAX_PLAUSIBLE_YEARS = 25

_TAG = re.compile(r"<[^>]*>")
_ENT = {"&nbsp;": " ", "&amp;": "&", "&#39;": "'", "&rsquo;": "'",
        "&quot;": '"', "&lsquo;": "'", "&ldquo;": '"', "&rdquo;": '"', "&ndash;": "-"}


def strip_html(h):
    """Replace tags with a SPACE, not '' -- otherwise block elements glue words
    together ('July 2027Major GPA') and \\b2027\\b silently stops matching."""
    s = _TAG.sub(" ", h or "")
    for k, v in _ENT.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip()


def auth_union(d):
    s = set()
    if d.get("RequiredWorkAuthName"):
        s.add(d["RequiredWorkAuthName"])
    for x in d.get("WorkAuthRequirements") or []:
        if x.get("Name"):
            s.add(x["Name"])
    return s


def _any(text, pats):
    return any(p.search(text) for p in pats)


def classify(d):
    title = d.get("JobTitle") or ""
    body = title + " || " + strip_html(d.get("Description"))
    rescued = _any(title, TITLE_RESCUE)

    if _any(title, TITLE_KILL):
        return None, "title is an internship/summer role"
    if _any(body, BODY_KILL):
        return None, "body describes an internship or 2028 grad"
    if not rescued and d.get("JobPostingJobTypeNames") == "Internship":
        return None, "job type = Internship"
    if not rescued and re.search(r"MBA INT", d.get("ContactName") or "", I):
        return None, "internship feed"

    u = auth_union(d)
    if not u:
        return None, "work auth not stated"
    if PERM in u:
        return None, "permanent US work auth required"
    if ALL_OK not in u:
        return None, "no explicit all-accepted"

    if _any(title, TITLE_POS):
        why, tier = "2027 in title", "firm"
    elif _any(body, BODY_POS):
        why, tier = "2027 grad/start requirement in description", "firm"
    else:
        # No stated year. Keep it as a softer "worth a look" tier if it is not
        # obviously a senior or experienced hire -- job descriptions are often
        # just silent about graduation year rather than genuinely irrelevant.
        if SENIOR.search(title):
            return None, "no 2027 signal (senior title)"
        yrs = [int(m) for m in YEARS.findall(body) if int(m) <= MAX_PLAUSIBLE_YEARS]
        if yrs and max(yrs) >= MAX_YEARS_FOR_MAYBE:
            return None, f"no 2027 signal ({max(yrs)}+ yrs experience)"
        why = (f"no year stated; {max(yrs)}-yr experience ask" if yrs
               else "no year stated; no seniority signal")
        tier = "maybe"

    return {
        "tier": tier,
        "id": str(d["Id"]),
        "employer": d.get("CompanyName") or "",
        "title": title,
        "deadline": d.get("ApplicationDeadlineDate"),
        "opened": d.get("ApplicationStartDate") or d.get("PostedDate"),
        "why": why,
        "auth_note": ("Sponsorship open; STEM-eligible degree required"
                      if STEM in u else "All work authorizations accepted"),
    }, why


def run(details):
    kept, rejected = [], {}
    for d in details.values():
        row, why = classify(d)
        (kept.append(row) if row else rejected.setdefault(why, []).append(
            f"{d.get('CompanyName')} | {(d.get('JobTitle') or '')[:44]}"))
    kept.sort(key=lambda r: r["deadline"] or "")
    return kept, rejected


if __name__ == "__main__":
    import json, pathlib
    DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
    details = json.loads((DATA / "details.json").read_text())
    kept, rejected = run(details)
    (DATA / "classified.json").write_text(json.dumps(kept, indent=1))
    print(f"kept {len(kept)} of {len(details)}")
    for why, lst in sorted(rejected.items(), key=lambda kv: -len(kv[1])):
        print(f"  rejected {len(lst):4d}  {why}")
