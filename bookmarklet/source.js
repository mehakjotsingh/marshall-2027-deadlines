/* Run from a logged-in 12twenty tab. Pulls open postings + details and saves
   a JSON file to ~/Downloads, which the local watcher picks up.
   Uses the page's own session -- nothing is stored, nothing bypasses anything. */
(async () => {
  const H = location.origin;
  if (!/marshall-usc\.12twenty\.com/.test(H)) {
    alert('Open a 12twenty tab first, then click this.');
    return;
  }
  const note = document.createElement('div');
  note.style.cssText = 'position:fixed;z-index:2147483647;top:14px;right:14px;background:#990000;' +
    'color:#fff;padding:11px 16px;border-radius:8px;font:14px system-ui;box-shadow:0 4px 14px rgba(0,0,0,.3)';
  note.textContent = 'Fetching listings...';
  document.body.appendChild(note);

  const payload = {
    ShouldCalculateTotal: true, PageNumber: 1, PageSize: 1000, IsSortAsc: false,
    sortBy: 1, locationFilter: 'City', StudentGroupIds: [],
    Filters: [{ SelectedIds: [3, 4], CustomFilterTypeId: 16, TypeId: 3,
                HasValue: true, IsExcluded: false, DisplayIndex: 10 }]
  };
  const r = await fetch(H + '/Api/V2/job-postings/post-query', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!r.ok) { note.textContent = 'Not signed in (HTTP ' + r.status + ')'; return; }
  const items = (await r.json()).Items || [];

  const keep = d => ({
    Id: d.Id, CompanyName: d.CompanyName, JobTitle: d.JobTitle,
    Description: d.Description, ApplicationDeadlineDate: d.ApplicationDeadlineDate,
    JobPostingJobTypeNames: d.JobPostingJobTypeNames, ContactName: d.ContactName,
    RequiredWorkAuthName: d.RequiredWorkAuthName,
    WorkAuthRequirements: d.WorkAuthRequirements, Url: d.Url
  });
  const out = [];
  for (let i = 0; i < items.length; i += 10) {
    await Promise.all(items.slice(i, i + 10).map(async it => {
      try {
        const d = await (await fetch(H + '/Api/V2/job-postings/' + it.Id)).json();
        out.push(keep(d));
      } catch (e) {}
    }));
    note.textContent = 'Fetching ' + out.length + ' / ' + items.length + '...';
  }

  const body = JSON.stringify({ pulled: new Date().toISOString(), postings: out });

  // Preferred path: hand off to the local receiver, so there is no file dialog.
  try {
    const resp = await fetch('http://127.0.0.1:8787/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body
    });
    if (resp.ok) {
      note.textContent = 'Sent ' + out.length + ' postings. Publishing...';
      setTimeout(() => note.remove(), 6000);
      return;
    }
  } catch (e) { /* receiver not running -- fall through to download */ }

  const blob = new Blob([body], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '12twenty-export.json';
  document.body.appendChild(a); a.click(); a.remove();
  note.textContent = 'Saved ' + out.length + ' postings to Downloads';
  setTimeout(() => note.remove(), 6000);
})();
