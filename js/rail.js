/**
 * The two side panes.
 *
 *   left  (#rail)    which text -- the siblings in this collection
 *   right (#onpage)  where in it -- this page's own headings
 *
 * Separate questions, so separate sides. Stacking them put Panchadasi's
 * chapters below thirty-one text names, which meant scrolling past the whole
 * collection to reach the thing you were actually reading.
 *
 * Neither pane names the collection: the rail only ever appears inside one,
 * and the home page is where you go to change collections.
 *
 * The rail's *structure* is in the page markup so nothing reflows on load;
 * this only fills it in. Pages with no headings simply get no second group.
 */
(function () {
  var DEV = '०१२३४५६७८९';
  var dev = function (n) {
    return String(n).split('').map(function (d) { return DEV[+d]; }).join('');
  };

  var root = (function () {
    var s = document.querySelector('script[src$="js/rail.js"]');
    return s && s.src
      ? new URL(s.src, location.href).href.replace(/js\/rail\.js(\?.*)?$/, '')
      : './';
  })();

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) { e.className = cls; }
    if (text != null) { e.textContent = text; }
    return e;
  }

  /** Which collection is this page in? body carries cat-<name>. */
  function category() {
    var m = /\bcat-([a-z]+)\b/.exec(document.body.className || '');
    return m && m[1] !== 'home' ? m[1] : null;
  }

  // ── group 1: sibling texts ───────────────────────────────────────────────

  /** 'प्रथमोऽध्यायः — अर्जुनविषादयोगः' -> 'अर्जुनविषादयोगः'.
   *  The ordinal only repeats the number shown beside it, and the rail is
   *  194px wide -- there is no room to say the same thing twice. */
  function shortName(s) {
    return s.indexOf('—') < 0 ? s : s.split('—').pop().trim();
  }

  /** One entry per page in the collection. A chaptered text has no page of
   *  its own, so it expands into its chapters. */
  function items(d) {
    var out = [];
    d.texts.forEach(function (t) {
      if (!t.chapters) {
        out.push({ file: t.file, label: t.dev || t.en });
        return;
      }
      var names = t.chapterNames || [];
      for (var i = 1; i <= t.chapters; i++) {
        out.push({
          file: t.chapterPrefix + i,
          n: i,
          label: names[i - 1] ? shortName(names[i - 1]) : ''
        });
      }
    });
    return out;
  }

  function texts(rail, cat) {
    fetch(root + 'data/' + cat + '.json')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var here = location.pathname.replace(/^.*\//, '').replace(/\.html$/, '');
        // no collection label -- the rail is only ever shown inside one
        // collection, and repeating it is what made the rail feel padded
        var box = el('div', 'rail-group');
        var list = el('ul', 'rail-list');

        items(d).forEach(function (it) {
          var li = el('li');
          var a = el('a', null, it.label);
          if (it.n) { a.insertBefore(el('span', 'tn', dev(it.n)), a.firstChild); }
          a.href = root + d.dir + '/' + it.file + '.html';
          if (it.file === here) { a.className = 'on'; }
          li.appendChild(a);
          list.appendChild(li);
        });
        box.appendChild(list);
        rail.insertBefore(box, rail.firstChild);
      })
      .catch(function () { /* rail just stays empty */ });
  }

  // ── group 2: this page's sections, as a grid ─────────────────────────────

  function sections(host) {
    var heads = Array.prototype.slice.call(
      document.querySelectorAll('h2.section-heading'));
    if (heads.length < 2) { return; }

    var box = el('div', 'rail-group');
    box.appendChild(el('div', 'rail-label', 'अध्यायाः'));
    var grid = el('ul', 'rail-list rail-sections');

    heads.forEach(function (h, i) {
      var li = el('li');
      var a = el('a', null, (h.textContent || '').trim());
      a.href = '#' + h.id;
      a.appendChild(el('span', 'rail-n', dev(i + 1)));
      li.appendChild(a);
      grid.appendChild(li);
    });
    box.appendChild(grid);
    host.appendChild(box);

    // mark the one you are currently inside
    var cells = grid.querySelectorAll('a');
    function sync() {
      var top = window.scrollY + 120, cur = 0;
      for (var i = 0; i < heads.length; i++) {
        if (heads[i].getBoundingClientRect().top + window.scrollY <= top) { cur = i; }
        else { break; }
      }
      for (var j = 0; j < cells.length; j++) {
        cells[j].classList.toggle('on', j === cur);
      }
    }
    var tick = false;
    window.addEventListener('scroll', function () {
      if (tick) { return; }
      tick = true;
      requestAnimationFrame(function () { sync(); tick = false; });
    }, { passive: true });
    sync();
  }

  // ── boot ─────────────────────────────────────────────────────────────────

  function mount() {
    var rail = document.getElementById('rail');      // left: which text
    var onpage = document.getElementById('onpage');  // right: where in it
    var cat = category();
    if (rail && cat) { texts(rail, cat); }
    if (onpage) { sections(onpage); }

    // The toolbar script-toggle.js builds sits right under the <h1>, which is
    // where these controls belong -- they act on the text below them. The
    // class links are plain markup now, so there is nothing left to fix up.
  }

  if (document.readyState === 'complete') {
    setTimeout(mount, 0);
  } else {
    document.addEventListener('DOMContentLoaded', mount);
  }
})();
