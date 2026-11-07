// Price guide finder: filters the pre-rendered guide by text (HK number, event, metal, date...).
// The page is complete without this script; it only hides what does not match.
(function () {
  var q = document.getElementById('gq');
  var items = Array.prototype.slice.call(document.querySelectorAll('[data-g]'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('[data-gg]'));
  var parts = Array.prototype.slice.call(document.querySelectorAll('[data-gp]'));
  var shown = document.getElementById('gshown');
  var none = document.getElementById('gnone');
  if (!q || !items.length) return;

  function norm(s) {
    return s.toLowerCase()
      .replace(/[‘’“”"]/g, '')
      .replace(/\bhk\s*[-#.]?\s*(?=\d)/g, 'hk')          // HK-449, hk 449, HK#449 -> hk449
      .replace(/[^a-z0-9&'\s-]/g, ' ');
  }
  var hay = items.map(function (el) {
    return norm((el.getAttribute('data-k') || '') + ' ' + el.textContent);
  });

  function apply() {
    var words = norm(q.value).split(/\s+/).filter(Boolean);
    var n = 0;
    items.forEach(function (el, i) {
      var ok = words.every(function (w) { return hay[i].indexOf(w) !== -1; });
      el.hidden = !ok;
      if (ok) n++;
    });
    groups.forEach(function (g) { g.hidden = !g.querySelector('[data-g]:not([hidden])'); });
    parts.forEach(function (p) { p.hidden = !p.querySelector('[data-g]:not([hidden])'); });
    if (shown) shown.textContent = n;
    if (none) none.hidden = n !== 0;
    var url = new URL(location.href);
    if (words.length) url.searchParams.set('q', q.value.trim()); else url.searchParams.delete('q');
    history.replaceState(null, '', url.pathname + url.search + url.hash);
  }

  q.addEventListener('input', apply);
  var params = new URLSearchParams(location.search);
  if (params.get('q')) { q.value = params.get('q'); apply(); }
})();
