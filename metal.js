// Live gold and silver for the Carr price guide.
// Rows for pieces that contain gold or silver carry their metal content (data-ag / data-au, troy
// ounces of fine metal) and, per grade, either the formula's premium over the metal (data-p =
// estimate, low, high: shown as metal + premium) or the formula's own figures (data-f: shown, but
// never below the metal). Prices traded around the clock, weekends included:
//   gold   = PAXG (one token = one troy ounce of gold) on Uniswap v3 (PAXG/USDC 0.05% pool),
//            30-minute time-weighted average, read through a public Ethereum node;
//   silver = the silver perpetual future on Hyperliquid (xyz:SILVER), mid price, public API.
// Chainlink's XAU/USD and XAG/USD feeds are the fallback for either, and the sanity check: a
// 24/7 price more than 10% (gold) or 15% (silver) from Chainlink's last price is not used.
// If nothing usable comes back, the page keeps the figures computed when the edition was built.
(function () {
  var rows = Array.prototype.slice.call(document.querySelectorAll('tr[data-ag], tr[data-au], tr[data-ptm]'));
  var note = document.getElementById('metal-live');
  if (!rows.length || !note || !window.fetch) return;

  var RPC = 'https://ethereum-rpc.publicnode.com';
  var GOLD = '0x214eD9Da11D2fbe465a6fc601a91E62EbEc1a0D6';    // Chainlink XAU / USD
  var SILVER = '0x379589227b15F1a12195D3f2d90bBc9F31f95235';  // Chainlink XAG / USD
  var PAXG_POOL = '0x5ae13baaef0620fdae1d355495dc51a17adb4082';  // Uniswap v3 PAXG (token0, 18 dp) / USDC (6 dp), 0.05%
  var HL = 'https://api.hyperliquid.xyz/info';
  function call(id, to, data) {
    return { jsonrpc: '2.0', id: id, method: 'eth_call', params: [{ to: to, data: data }, 'latest'] };
  }
  function word(n) { return n.toString(16).padStart(64, '0'); }
  function signed(h) { var v = BigInt('0x' + h); return v >= (BigInt(1) << BigInt(255)) ? v - (BigInt(1) << BigInt(256)) : v; }
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

  var TWAP = 1800;
  var body = [call(1, GOLD, '0xfeaf968c'), call(2, SILVER, '0xfeaf968c'), call(3, GOLD, '0x313ce567'), call(4, SILVER, '0x313ce567'),
              call(5, PAXG_POOL, '0x883bdbfd' + word(32) + word(2) + word(TWAP) + word(0)),   // observe([1800, 0])
              call(6, PAXG_POOL, '0x3850c7bd')];                                               // slot0: spot, if observe fails
  var chain = fetch(RPC, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    .then(function (r) { return r.json(); });
  var perp = fetch(HL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'allMids', dex: 'xyz' }) })
    .then(function (r) { return r.json(); })
    .then(function (m) { return Number(m && m['xyz:SILVER']); })
    .catch(function () { return NaN; });
  Promise.all([chain, perp])
    .then(function (both) {
      var res = both[0], by = {};
      res.forEach(function (x) { by[x.id] = x.result; });
      function feed(round, dec) {
        var w = round.slice(2), d = parseInt(dec, 16);
        return { price: parseInt(w.slice(64, 128), 16) / Math.pow(10, d), t: parseInt(w.slice(192, 256), 16) };
      }
      var cg = { price: 0, t: 0 }, cs = { price: 0, t: 0 };
      try { cg = feed(by[1], by[3]); cs = feed(by[2], by[4]); } catch (e) { /* no Chainlink: 24/7 prices only */ }
      var now = Date.now() / 1000, fresh = now - Math.min(cg.t, cs.t) < 4 * 86400;
      var paxg = NaN, paxgHow = '30-minute average';
      try {                                                  // 30-minute average from the pool's tick record
        var w = by[5].slice(2);
        var tick = Number(signed(w.slice(256, 320)) - signed(w.slice(192, 256))) / TWAP;
        paxg = Math.pow(1.0001, tick) * 1e12;
      } catch (e) {
        try { var sp = Number(BigInt('0x' + by[6].slice(2, 66))) / Math.pow(2, 96); paxg = sp * sp * 1e12; paxgHow = 'latest pool price'; } catch (e2) { paxg = NaN; }
      }
      function near(x, ref, tol) { return x > 0 && (!(ref > 0) || Math.abs(x / ref - 1) <= tol); }
      var g = { price: cg.price, src: 'chainlink', t: cg.t }, s = { price: cs.price, src: 'chainlink', t: cs.t };
      if (near(paxg, cg.price, 0.10)) g = { price: paxg, src: 'paxg', t: now };
      if (near(both[1], cs.price, 0.15)) s = { price: both[1], src: 'perp', t: now };
      if (!(g.price > 0 && s.price > 0) || ((g.src === 'chainlink' || s.src === 'chainlink') && !fresh)) throw new Error('no usable price');
      g.price = Math.round(g.price * 100) / 100; s.price = Math.round(s.price * 1000) / 1000;
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
      // the reader's own time zone, named; Mountain time when the browser gives none (or only UTC, as privacy modes do)
      var tz, opts = { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short' };
      try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) { tz = ''; }
      if (!tz || /^(Etc\/)?(UTC|GMT)$/.test(tz)) opts.timeZone = 'America/Denver';
      function when(ts) { return new Date(ts * 1000).toLocaleString('en-US', opts); }
      var SRC = {
        paxg: 'gold is the trading price on Uniswap of PAXG, a token its issuer, Paxos, backs with one troy ounce of gold (' + paxgHow + ')',
        perp: 'silver is the price of the silver perpetual future on Hyperliquid'
      };
      var parts = [];
      if (g.src === 'paxg') parts.push(SRC.paxg); else parts.push('gold is Chainlink\'s gold price (updated ' + when(g.t) + ')');
      if (s.src === 'perp') parts.push(SRC.perp); else parts.push('silver is Chainlink\'s silver price (updated ' + when(s.t) + ')');
      note.innerHTML = '<strong>Gold ' + ounce(g.price) + ' &middot; silver ' + ounce(s.price) + ' an ounce</strong>, live as of ' + when(now) +
        ': ' + parts.join('; ') + '.' + (g.src !== 'chainlink' && s.src !== 'chainlink' ? ' Both trade around the clock, weekends included.' : '') +
        ' Figures for pieces containing gold or silver include their metal at these prices.';
      note.classList.add('live');
    })
    .catch(function () { /* keep the build-time figures; the note already says which prices they use */ });
})();
