// Library finder: filters the pre-rendered shelves by text and subject chips.
// The search box sits in the home-page hero; the hint under it reports matches and links down to them.
// The page is complete without this script; it only hides what does not match.
(function () {
  var q = document.getElementById('q');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var shelves = Array.prototype.slice.call(document.querySelectorAll('.shelf'));
  var items = Array.prototype.slice.call(document.querySelectorAll('.entries li'));
  var shown = document.getElementById('shown');
  var noMatch = document.getElementById('no-match');
  var hint = document.getElementById('hero-hint');
  var form = document.getElementById('hero-search');
  var subjects = document.querySelector('details.subjects');
  if (!q || !items.length) return;
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function toLibrary() {
    var lib = document.getElementById('library');
    if (lib) lib.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
  }

  var active = null;
  var hay = items.map(function (li) {
    return (li.textContent + ' ' + (li.getAttribute('data-tags') || '').replace(/\|/g, ' ')).toLowerCase();
  });
  var tagsOf = items.map(function (li) {
    return (li.getAttribute('data-tags') || '').split('|');
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
    if (hint) {
      hint.hidden = !(words.length || active);
      hint.innerHTML = n ? '<a href="#library">' + n + (n === 1 ? ' match' : ' matches') + ' in the library</a>' : 'No matches in the library';
    }
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
  if (form) form.addEventListener('submit', function (e) { e.preventDefault(); apply(); toLibrary(); });

  var params = new URLSearchParams(location.search);
  if (params.get('q')) q.value = params.get('q');
  if (params.get('tag')) {
    chips.forEach(function (c) {
      if (c.getAttribute('data-tag') === params.get('tag')) { active = params.get('tag'); c.setAttribute('aria-pressed', 'true'); }
    });
    if (active && subjects) subjects.open = true;
  }
  if (q.value || active) apply();
})();
