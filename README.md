# Marshall 2027 Recruiting Deadlines

Calendar feed of **on-cycle, full-time roles for the USC Marshall Class of 2027
that are open to visa sponsorship**, screened from 12twenty.

Subscribe once; new postings appear in your calendar automatically:

```
webcal://mehakjotsingh.github.io/marshall-2027-deadlines/deadlines.ics
```

## Why the data pull is a click, not a cron job

Three independent walls make unattended scraping impossible:

1. 12twenty sits behind **USC Shibboleth SSO with Duo MFA**, which cannot be automated.
2. A Playwright-driven browser is **challenged by Cloudflare** bot detection.
3. **Chrome 136+ refuses `--remote-debugging-port` on the default profile**, so
   automation cannot attach to the real signed-in Chrome either.

Getting past any of those would mean defeating bot detection, which this project
does not do. So the pull is one bookmarklet click in your own browser, using the
session you already have. Everything after the click is automatic: a launchd
watcher on `~/Downloads` ingests the export, screens it, rebuilds the calendar,
commits, pushes, and posts a macOS notification.

Open `bookmarklet/install.html` and drag the button to your bookmarks bar.

## Screening rules

No LLM. Two independent gates, both derived from live data.

**1. Work authorization.** 12twenty states the requirement in two places -- a
scalar (`RequiredWorkAuthName`) and a list (`WorkAuthRequirements`). They
disagree on a handful of postings. We take the union and apply the stricter
reading: keep only if *All Work Authorizations Accepted* is present **and**
*Permanent US Work Authorization Required* is absent from both. On the first run
this gate alone cut 299 postings to 140.

**2. Cycle.** Separates on-cycle Class-of-2027 hiring from just-in-time postings
and Class-of-2028 internships.

Employer metadata is **not** trusted as a hard filter -- Gartner tags a full-time
role for 2027 graduates as an `Internship`. Metadata rejections are therefore
overridable by an explicit graduate-year phrase in the title, while internship
wording in the title or body never is. Banking internships titled
*Summer Associate* are rejected by name, since they never say "intern".

### Gotchas encoded in the rules

- **HTML stripping must insert a space**, not the empty string. Block elements
  otherwise glue words together (`July 2027Major GPA`) and `\b2027\b` silently
  stops matching. This caused a real false negative during development.
- **Deadlines are stored in UTC.** `06:59Z` is `23:59` the previous day in
  Pacific; slicing the date off the raw value reports every deadline a day late.
- **A structural filter that looks right is wrong.** `ExternalJobPostingSourceId`
  distinguishes aggregator-sourced from school-posted listings, but *not*
  on-cycle from just-in-time -- most real on-cycle roles arrive via the aggregator.

`scripts/test_classify.py` pins all of the above. Run it before changing rules.

## Layout

| Path | Purpose |
|---|---|
| `bookmarklet/install.html` | Drag-to-install the export button |
| `bookmarklet/source.js` | Readable source for the bookmarklet |
| `scripts/ingest.py` | Picks up the newest export from `~/Downloads` |
| `scripts/classify.py` | The screening rules |
| `scripts/build.py` | Emits `docs/deadlines.ics` + `docs/index.html` |
| `scripts/test_classify.py` | Regression tests |
| `run.sh` | Ingest, classify, build, commit, push, notify |
| `docs/` | Published by GitHub Pages |

Launch agents: `com.mehakjot.marshall2027.watch` (watches `~/Downloads`) and
`com.mehakjot.marshall2027.remind` (Monday 07:00 nudge).
