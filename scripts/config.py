"""Shared config. Base URL and the authenticated API endpoints."""
BASE   = "https://marshall-usc.12twenty.com"
SEARCH = f"{BASE}/Api/V2/job-postings/post-query"
DETAIL = f"{BASE}/Api/V2/job-postings/{{id}}"
JOB_URL = f"{BASE}/jobPostings#/jobPostings/{{id}}"

# Status filter: 3 = Approved, 4 = Application Open (CustomFilterTypeId 16)
SEARCH_PAYLOAD = {
    "ShouldCalculateTotal": True,
    "PageNumber": 1,
    "PageSize": 1000,
    "IsSortAsc": False,
    "sortBy": 1,
    "locationFilter": "City",
    "StudentGroupIds": [],
    "Filters": [{
        "SelectedIds": [3, 4],
        "CustomFilterTypeId": 16,
        "TypeId": 3,
        "HasValue": True,
        "IsExcluded": False,
        "DisplayIndex": 10,
    }],
}
PROFILE_DIR = "chrome-profile"
LOGIN_PROBE = f"{BASE}/jobPostings#/jobPostings/index?viewId=1&tab=all"
