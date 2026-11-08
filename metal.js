// Live gold and silver for the Carr price guide.
// Rows for pieces that contain gold or silver carry their metal content (data-ag / data-au, troy
// ounces of fine metal) and, per grade, either the formula's premium over the metal (data-p =
// estimate, low, high: shown as metal + premium) or the formula's own figures (data-f: shown, but
// never below the metal). This reads Chainlink's XAU/USD and XAG/USD feeds on Ethereum through a public node
// and shows premium + metal at today's price. Without it (or if the feed is unreachable or more
// than four days old) the page keeps the figures computed when the edition was built.
(function () {
  var rows = Array.prototype.slice.call(document.querySelectorAll('tr[data-ag], tr[data-au], tr[data-ptm]'));
  var note = document.getElementById('metal-live');
  if (!rows.length || !note || !window.fetch) return;

  var RPC = 'https://ethereum-rpc.publicnode.com';
  var GOLD = '0x214eD9Da11D2fbe465a6fc601a91E62EbEc1a0D6';    // XAU / USD
  var SILVER = '0x379589227b15F1a12195D3f2d90bBc9F31f95235';  // XAG / USD
  function call(id, to, data) {
    return { jsonrpc: '2.0', id: id, method: 'eth_call', params: [{ to: to, data: data }, 'latest'] };
  }
  // same rounding as the guide's build script, never below `floor` (the metal a piece contains)
  var STEPS = [[20, 1], [100, 5], [500, 10], [2000, 25], [10000, 100], [Infinity, 500]];
  function stepFor(x) { for (var i = 0; i < STEPS.length; i++) if (x < STEPS[i][0]) return STEPS[i][1]; }
  function nice(x, floor) {
    var s = stepFor(x), v = Math.max(s, Math.round(x / s) * s);
    if (floor && v < floor) { var fs = stepFor(floor); v = Math.ceil(floor / fs) * fs; }
    return v;
  }
  function money(v) { return '$' + v.toLocaleString('en-US'); }
  function ounce(v) { return '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }

  var body = [call(1, GOLD, '0xfeaf968c'), call(2, SILVER, '0xfeaf968c'), call(3, GOLD, '0x313ce567'), call(4, SILVER, '0x313ce567')];
  fetch(RPC, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    .then(function (r) { return r.json(); })
    .then(function (res) {
      var by = {};
      res.forEach(function (x) { by[x.id] = x.result; });
      function feed(round, dec) {
        var w = round.slice(2), d = parseInt(dec, 16);
        return { price: parseInt(w.slice(64, 128), 16) / Math.pow(10, d), t: parseInt(w.slice(192, 256), 16) };
      }
      var g = feed(by[1], by[3]), s = feed(by[2], by[4]);
      var now = Date.now() / 1000;
      if (!(g.price > 0 && s.price > 0) || now - Math.min(g.t, s.t) > 4 * 86400) throw new Error('stale feed');
      rows.forEach(function (tr) {
        var melt = parseFloat(tr.getAttribute('data-ag') || '0') * s.price + parseFloat(tr.getAttribute('data-au') || '0') * g.price
          + parseFloat(tr.getAttribute('data-ptm') || '0');          // platinum: fixed, latest monthly price
        Array.prototype.forEach.call(tr.querySelectorAll('td[data-p], td[data-f]'), function (td) {
          var v;
          if (td.hasAttribute('data-p')) {                 // metal + premium
            v = td.getAttribute('data-p').split(',').map(function (x) { return melt + Number(x); });
          } else {                                         // formula figure, never below the metal
            v = td.getAttribute('data-f').split(',').map(function (x) { return Math.max(Number(x), melt); });
            v[2] = Math.max(v[2], v[0]);
          }
          var est = td.querySelector('.est'), rng = td.querySelector('.rng');
          if (est) est.textContent = money(nice(v[0], melt));
          if (rng) rng.textContent = money(nice(v[1], melt)) + '–' + money(nice(v[2], melt));
        });
      });
      var when = new Date(Math.max(g.t, s.t) * 1000);
      // the reader's own time zone, named; Mountain time when the browser gives none (or only UTC, as privacy modes do)
      var tz, opts = { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short' };
      try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) { tz = ''; }
      if (!tz || /^(Etc\/)?(UTC|GMT)$/.test(tz)) opts.timeZone = 'America/Denver';
      note.innerHTML = '<strong>Gold ' + ounce(g.price) + ' &middot; silver ' + ounce(s.price) + ' an ounce</strong>, live from Chainlink (updated ' +
        when.toLocaleString('en-US', opts) +
        '). Figures for pieces containing gold or silver include their metal at these prices.';
      note.classList.add('live');
    })
    .catch(function () { /* keep the build-time figures; the note already says which prices they use */ });
})();
