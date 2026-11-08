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
    return { ref: hit.r, abbr: hit.a, raw: s, rest: hit.head.test(s) ? s.replace(hit.head, '') : '' };
  }

  // Pieces in our price guide (built with the site: /decoder/pieces.json): an HK number or a Moonlight Mint
  // catalogue number we price shows the piece itself, its page and our estimate range, not only the book.
  var piecesP = null, seq = 0;
  function pieceIndex() {
    if (!piecesP) piecesP = fetch('/decoder/pieces.json').then(function (r) { return r.json(); }).catch(function () { return null; });
    return piecesP;
  }
  function normCarr(s) { return s.trim().toUpperCase().replace(/[\s\-_]+/g, '_').replace(/^_+|_+$/g, ''); }
  function pieceCard(e) {          // [page, label, low, high, what the figure rests on, slab or raw]
    return '<div class="piece-card"><p class="eyebrow">In our price guide</p>' +
      '<h3><a href="' + esc(e[0]) + '">' + esc(e[1]) + '</a></h3>' +
      '<p>Our estimated value: <strong>' + esc(e[2]) + ' to ' + esc(e[3]) + '</strong> by grade, ' + esc(e[5]) + '. ' +
      '<span class="cite">' + esc(e[4]) + '.</span>' +
      (e[6] ? ' <span class="cite">At this edition&rsquo;s metal prices; the piece&rsquo;s page shows them at the live price.</span>' : '') + '</p>' +
      '<p class="lookup"><a href="' + esc(e[0]) + '">Values by grade for this piece</a> &middot; our opinion of value, not an offer</p></div>';
  }
  function addPiece(raw, d, my) {
    var isHK = d && d.ref.id === 'hk';
    if (!isHK && !/[_\d]/.test(raw)) return;
    pieceIndex().then(function (idx) {
      if (!idx || my !== seq) return;                     // index unavailable, or the box changed meanwhile
      var e = isHK ? idx.hk[d.rest.toLowerCase().replace(/[^a-z0-9]/g, '')] : idx.carr[normCarr(raw)];
      if (!e) return;
      if (!d) {                                           // a Moonlight Mint number: no reference book uses it
        out.className = 'decoded hit';
        out.innerHTML = '<p class="eyebrow"><span class="num">' + esc(raw.trim()) + '</span> is a Moonlight Mint (Daniel Carr) catalogue number</p>';
      }
      out.insertAdjacentHTML(d ? 'afterbegin' : 'beforeend', pieceCard(e));
    });
  }

  function render(raw) {
    var my = ++seq;
    if (!raw.trim()) { out.hidden = true; out.innerHTML = ''; return; }
    var d = decode(raw);
    addPiece(raw, d, my);
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
      (r.find_url ? '<p class="lookup">Find the book: <a href="' + esc(r.find_url) + '" rel="noopener">' + r.find_label + '</a>' + (r.find_note ? ' <span class="cite">' + r.find_note + '</span>' : '') + '</p>'
                  : (r.find_note ? '<p class="lookup"><span class="cite">' + r.find_note + '</span></p>' : '')) +
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
