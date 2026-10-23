// Catalog-number decoder: "HK-449" -> which reference, what it covers, where to look it up.
// The full table is rendered on the page already; this adds the lookup box.
(function () {
  var dataEl = document.getElementById('refs-data');
  var input = document.getElementById('code');
  var out = document.getElementById('decoded');
  if (!dataEl || !input || !out) return;
  var refs = JSON.parse(dataEl.textContent);


  // One matcher per abbreviation: the letters in order, any separators between
  // them, and then a digit, a non-letter or the end. So "HK-449", "hk449" and
  // "H.K. 449" all decode to HK, while "Elder 3" does not decode to Eimer's "E".
  var SEP = "[\\s.\\-\u2013\u2014_'\u2019]*";
  function pattern(a) {
    var chars = a.toLowerCase().split('').filter(function (c) { return /[a-z0-9&]/.test(c); });
    return chars.map(function (c) { return c === '&' ? '&' : c; }).join(SEP);
  }
  var keys = [];
  refs.forEach(function (r) {
    r.abbr.concat(r.aliases || []).forEach(function (a) {
      var p = pattern(a);
      keys.push({ len: p.length, r: r, a: a,
        head: new RegExp('^' + p + '(?=[^a-z]|$)', 'i'),
        body: new RegExp('(^|[^a-z])' + p + '(?=[^a-z]|$)', 'i'),
        letters: a.replace(/[^a-z0-9]/gi, '').length });
    });
  });
  keys.sort(function (x, y) { return y.len - x.len; });

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function decode(raw) {
    var s = raw.trim();
    if (!s) return null;
    var i, hit = null;
    for (i = 0; i < keys.length; i++) {
      if (keys[i].head.test(s)) { hit = keys[i]; break; }
    }
    if (!hit) {
      for (i = 0; i < keys.length; i++) {
        if (keys[i].letters >= 3 && keys[i].body.test(s)) { hit = keys[i]; break; }
      }
    }
    if (!hit) return null;
    return { ref: hit.r, abbr: hit.a, raw: s };
  }

  function render(raw) {
    if (!raw.trim()) { out.hidden = true; out.innerHTML = ''; return; }
    var d = decode(raw);
    if (!d) {
      out.hidden = false;
      out.className = 'decoded miss';
      out.innerHTML = '<p>No reference on this page uses <strong>' + esc(raw.trim()) + '</strong>. The table below lists every abbreviation we know. If a dealer or auction house is using one we are missing, <a href="mailto:brian@puebloip.com?subject=Decoder">tell us</a>.</p>';
      return;
    }
    var r = d.ref;
    var lookup = '';
    if (r.lookup_url) {
      lookup = '<p class="lookup">Look it up: <a href="' + esc(r.lookup_url) + '" rel="noopener">' + esc(r.lookup_label) + '</a></p>';
    } else {
      lookup = '<p class="lookup">Printed reference only; no online lookup that we know of.</p>';
    }
    out.hidden = false;
    out.className = 'decoded hit';
    out.innerHTML =
      '<p class="eyebrow"><span class="num">' + esc(d.raw) + '</span> is a ' + esc(d.abbr) + ' number from</p>' +
      '<h3>' + esc(r.title) + '</h3>' +
      '<p class="cite">' + esc(r.citation) + '</p>' +
      '<p>' + r.covers + ' Numbers look like <code>' + esc(r.example) + '</code>.</p>' +
      (r.notes ? '<p>' + r.notes + '</p>' : '') +
      lookup +
      '<p class="rowlink"><a href="#ref-' + esc(r.id) + '">Row in the table</a></p>';
  }

  input.addEventListener('input', function () { render(input.value); });
  var p = new URLSearchParams(location.search).get('n');
  if (p) { input.value = p; render(p); }
  document.getElementById('decoder-form').addEventListener('submit', function (e) {
    e.preventDefault();
    render(input.value);
    var url = new URL(location.href);
    if (input.value.trim()) url.searchParams.set('n', input.value.trim()); else url.searchParams.delete('n');
    history.replaceState(null, '', url.pathname + url.search);
  });
})();
