// Library finder: filters the pre-rendered shelves by text and subject chips.
// The page is complete without this script; it only hides what does not match.
(function () {
  var q = document.getElementById('q');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var shelves = Array.prototype.slice.call(document.querySelectorAll('.shelf'));
  var items = Array.prototype.slice.call(document.querySelectorAll('.entries li'));
  var shown = document.getElementById('shown');
  var noMatch = document.getElementById('no-match');
  if (!q || !items.length) return;

  var active = null;
  var hay = items.map(function (li) {
    return (li.textContent + ' ' + (li.getAttribute('data-tags') || '')).toLowerCase();
  });
  var tagsOf = items.map(function (li) {
    return (li.getAttribute('data-tags') || '').split(/\s+/);
  });

  function norm(s) { return s.toLowerCase().replace(/[^a-z0-9&'\s-]/g, ' ').trim(); }

  function apply() {
    var words = norm(q.value).split(/\s+/).filter(Boolean);
    var n = 0;
    items.forEach(function (li, i) {
      var ok = words.every(function (w) { return hay[i].indexOf(w) !== -1; });
      if (ok && active) ok = tagsOf[i].indexOf(active) !== -1;
      li.hidden = !ok;
      if (ok) n++;
    });
    shelves.forEach(function (s) {
      var any = Array.prototype.some.call(s.querySelectorAll('.entries li'), function (li) { return !li.hidden; });
      s.hidden = !any;
    });
    if (shown) shown.textContent = n;
    if (noMatch) noMatch.hidden = n !== 0;
    var url = new URL(location.href);
    if (words.length) url.searchParams.set('q', q.value.trim()); else url.searchParams.delete('q');
    if (active) url.searchParams.set('tag', active); else url.searchParams.delete('tag');
    history.replaceState(null, '', url.pathname + url.search + url.hash);
  }

  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      var t = c.getAttribute('data-tag');
      active = active === t ? null : t;
      chips.forEach(function (o) { o.setAttribute('aria-pressed', String(o.getAttribute('data-tag') === active)); });
      apply();
    });
  });
  q.addEventListener('input', apply);

  var params = new URLSearchParams(location.search);
  if (params.get('q')) q.value = params.get('q');
  if (params.get('tag')) {
    chips.forEach(function (c) {
      if (c.getAttribute('data-tag') === params.get('tag')) { active = params.get('tag'); c.setAttribute('aria-pressed', 'true'); }
    });
  }
  if (q.value || active) apply();
})();
