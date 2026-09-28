# Marshall 2027 Recruiting Deadlines

Auto-updated calendar feed of **on-cycle, full-time roles for the USC Marshall
Class of 2027 that are open to visa sponsorship**, scraped weekly from 12twenty.

Subscribe once and new postings appear in your calendar automatically:

```
webcal://<user>.github.io/marshall-2027-deadlines/deadlines.ics
```

## Why the scrape runs locally

12twenty sits behind USC Shibboleth SSO with Duo MFA, which cannot be automated.
A GitHub Actions runner cannot log in. So the scrape runs on a Mac against a
Playwright profile that was signed in once by hand; GitHub only serves the output.

Sessions expire every few weeks. `run.sh` detects the 401, sends a macOS
notification, and exits 2. Re-authenticate with:

```bash
./.venv/bin/python scripts/scrape.py --login
```

## Screening rules

No LLM is used. Two independent gates, both derived from the live data:

**1. Work authorization.** 12twenty states the requirement in two places — a
scalar (`RequiredWorkAuthName`) and a list (`WorkAuthRequirements`). They
disagree on a handful of postings. We take the union and apply the stricter
reading: keep only if *All Work Authorizations Accepted* is present **and**
*Permanent US Work Authorization Required* is absent from both. On the first
run this alone cut 299 postings to 140.

**2. Cycle.** Distinguishes on-cycle Class-of-2027 hiring from just-in-time
postings and from Class-of-2028 internships.

Employer-supplied metadata is **not** trusted as a hard filter — Gartner tags a
full-time role for 2027 graduates as an `Internship`. So metadata rejections are
overridable by an explicit graduate-year phrase in the title, while internship
wording in the title or body never is. Banking internships titled
*Summer Associate* are rejected explicitly, since they never say "intern".

### Gotchas encoded in the rules

- **HTML stripping must insert a space**, not the empty string. Block elements
  otherwise glue words together (`July 2027Major GPA`), and `\b2027\b` silently
  stops matching. This cost a real false negative during development.
- **Deadlines are stored in UTC.** `06:59Z` is `23:59` the previous day in
  Pacific. Slicing the date string off the raw value reports every deadline a
  day late.

## Layout

| Path | Purpose |
|---|---|
| `scripts/scrape.py` | Playwright + persisted session; exits 2 on expiry |
| `scripts/classify.py` | The screening rules |
| `scripts/build.py` | Emits `docs/deadlines.ics` + `docs/index.html` |
| `run.sh` | Orchestrates, commits, pushes, notifies |
| `docs/` | Published by GitHub Pages |

Scheduled by `~/Library/LaunchAgents/com.mehakjot.marshall2027.plist`
(Mondays 07:00; launchd catches up if the Mac was asleep).
