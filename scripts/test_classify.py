"""Regression tests locking in the traps found while building this."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import classify as C

ALL = [{"Name": "All Work Authorizations Accepted"}]
PERM = [{"Name": "Permanent US Work Authorization Required"}]
STEM = [{"Name": "All Work Authorizations Accepted"}, {"Name": "STEM Eligible Degree"}]


def P(**kw):
    d = {"Id": 1, "CompanyName": "X", "JobTitle": "", "Description": "",
         "ApplicationDeadlineDate": "2026-10-16T06:59:00",
         "JobPostingJobTypeNames": "Job", "ContactName": "",
         "RequiredWorkAuthName": "All Work Authorizations Accepted",
         "WorkAuthRequirements": ALL}
    d.update(kw)
    return d


CASES = [
 # (label, posting, expect_kept)
 ("2027 in title", P(JobTitle="2027 MBA University Graduate - Product Manager"), True),

 ("HTML block tags glue words: 'July 2027Major' must still match",
  P(JobTitle="Analyst", Description="<p>Graduation Date between December 2026 and July 2027</p><p>Major GPA of 3.0</p>"), True),

 ("program-year title 2026/2027", P(JobTitle="XPS Leadership Program 2026/2027"), True),

 ("mis-tagged Internship is rescued by '2027 Graduates' in title",
  P(JobTitle="Account Manager (2027 Graduates)", JobPostingJobTypeNames="Internship"), True),

 ("banking 'Summer Associate' is an internship even without the word intern",
  P(JobTitle="2027 | Americas | Houston | Investment Banking | Summer Associate"), False),

 ("Spring 2027 internship rejected", P(JobTitle="FX Original Programming Intern, Spring 2027"), False),

 ("2028 grad rejected",
  P(JobTitle="MBA Program", Description="MBA students graduating between September 2027 and July 2028"), False),

 ("scalar says all-accepted but list says permanent -> reject (stricter wins)",
  P(JobTitle="Role 2027", RequiredWorkAuthName="All Work Authorizations Accepted",
    WorkAuthRequirements=ALL + PERM), False),

 ("list says all-accepted but scalar says permanent -> reject",
  P(JobTitle="Role 2027", RequiredWorkAuthName="Permanent US Work Authorization Required",
    WorkAuthRequirements=ALL), False),

 ("STEM conditional is kept but flagged",
  P(JobTitle="Associate 2027", RequiredWorkAuthName="All Work Authorizations Accepted",
    WorkAuthRequirements=STEM), True),

 ("no work auth stated -> reject", P(JobTitle="Role 2027", RequiredWorkAuthName=None,
                                     WorkAuthRequirements=[]), False),

 ("no 2027 signal -> reject", P(JobTitle="Senior Finance Manager",
                                Description="MBA preferred. 7+ years experience."), False),

 ("degree-completion phrasing (World Bank)",
  P(JobTitle="Young Professional Program", Description="Completion of a masters-level degree "
    "in a relevant field, or a higher qualification, before September 1, 2027"), True),

 ("enrolled during Fall 2027 -> class of 2028, reject",
  P(JobTitle="MBA Summer Role 2027", Description="Must be enrolled at a university during the "
    "Fall 2027 semester"), False),
]

fails = 0
for label, posting, expect in CASES:
    row, why = C.classify(posting)
    got = row is not None
    ok = got == expect
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"      expected kept={expect}, got kept={got} ({why})")

row, _ = C.classify(P(JobTitle="Associate 2027", WorkAuthRequirements=STEM))
if "STEM" not in (row or {}).get("auth_note", ""):
    print("FAIL  STEM flag not surfaced in auth_note"); fails += 1
else:
    print("PASS  STEM flag surfaced in auth_note")

print(f"\n{len(CASES)+1-fails}/{len(CASES)+1} passed")
sys.exit(1 if fails else 0)
