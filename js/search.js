/**
 * Search: type an English name, land on the text. Optionally with a reference.
 *
 *     kena              -> upanishads/kena.html
 *     cha 7.25          -> upanishads/chandogya.html   scrolled to 7.25
 *     gita 2.47         -> gita/adhyaya-2.html         scrolled to verse 47
 *     viveka 51         -> prakarana/vivekachudamani.html scrolled to verse 51
 *
 * Opened from the home page input, the toolbar button, or "/".
 *
 * The index is split one file per category so each stays small and hand-
 * editable; see data/categories.json for the list. Nothing per-verse is
 * stored -- a reference is resolved against the target page's own markup,
 * which already carries every heading id and every printed verse number.
 */
(function () {
  var DEV = '०१२३४५६७८९';

  // Site root, taken from this script's own URL rather than guessed from the
  // page's path depth. The guess broke on GitHub Pages, which serves the site
  // from /grantha/ while a local server serves it from / -- the home page then
  // resolved "../data" to the domain root and 404'd.
  var root = (function () {
    var s = document.currentScript ||
            document.querySelector('script[src$="js/search.js"]');
    if (!s || !s.src) { return './'; }
    // new URL() collapses any ".." segments, so this holds whether the tag
    // said "js/search.js" or "../js/search.js".
    return new URL(s.src, location.href).href
      .replace(/js\/search\.js(\?.*)?$/, '');
  })();

  function toDev(s) {
    return String(s).replace(/\d/g, function (d) { return DEV[+d]; });
  }
  function fromDev(s) {
    return String(s).replace(/[०-९]/g, function (d) { return DEV.indexOf(d); });
  }
  function norm(s) {
    return String(s).toLowerCase().replace(/[^a-z0-9]/g, '');
  }

  // ── reference resolution on the target page ──────────────────────────────

  /**
   * Scroll to `ref` ("7.25", "47") using whatever this page actually provides:
   * a printed verse number, else a known heading id shape. Returns false if
   * neither matches -- the caller reports that rather than guessing.
   */
  function goToRef(ref) {
    if (!ref) { return false; }
    var parts = ref.split('.').map(Number);
    var devRef = toDev(ref);

    // 1. a verse whose printed number is exactly this
    var nums = document.querySelectorAll('.verse-num');
    for (var i = 0; i < nums.length; i++) {
      if (fromDev(nums[i].textContent).replace(/[॥\s]/g, '') === ref) {
        return reveal(nums[i].closest('.verse') || nums[i]);
      }
    }

    // 2. heading anchors, in the shapes this site generates
    var ids = [];
    if (parts.length >= 2) {
      ids.push('ch-' + parts[0] + '-s-' + parts[1],
               'pada-' + parts[0] + '-adh-' + parts[1]);
    }
    ids.push('section-' + parts[0], 'ch-' + parts[0], 'pada-' + parts[0]);
    for (var j = 0; j < ids.length; j++) {
      var h = document.getElementById(ids[j]);
      if (h) { return reveal(h); }
    }

    // Deliberately no ordinal fallback. ".verse" also wraps shanti mantras,
    // colophons and उवाच labels, so the Nth block is not the Nth verse -- e.g.
    // Atmabodha prints 1..68 but has 69 blocks. Guessing would answer
    // "atmabodha 69" with the colophon instead of admitting there is no 69.
    // Any number actually printed on the page is already caught above.
    return false;
  }

  /** Say a reference does not exist, rather than scrolling somewhere plausible. */
  function notFound(ref) {
    var n = document.querySelector('.search-note');
    if (!n) {
      n = document.createElement('div');
      n.className = 'search-note';
      document.body.appendChild(n);
    }
    n.textContent = 'No ' + ref + ' on this page';
    n.hidden = false;
    clearTimeout(notFound._t);
    notFound._t = setTimeout(function () { n.hidden = true; }, 3200);
  }

  function reveal(node) {
    node.scrollIntoView({ behavior: 'smooth', block: 'start' });
    node.classList.add('search-hit');
    setTimeout(function () { node.classList.remove('search-hit'); }, 2200);
    return true;
  }

  // ── index ────────────────────────────────────────────────────────────────

  var texts = null, loading = null;

  function load() {
    if (texts) { return Promise.resolve(texts); }
    if (loading) { return loading; }
    loading = fetch(root + 'data/categories.json')
      .then(function (r) { return r.json(); })
      .then(function (man) {
        // manifest carries tiers now; the list of collections is under .categories
        var cats = man.categories || man;
        return Promise.all(cats.map(function (c) {
          return fetch(root + 'data/' + c + '.json').then(function (r) { return r.json(); });
        }));
      })
      .then(function (files) {
        texts = [];
        files.forEach(function (f) {
          f.texts.forEach(function (t) {
            texts.push({
              dir: f.dir,
              label: f.label,
              tier: f.tier,          // colours the row in the results list
              file: t.file,
              dev: t.dev,
              en: t.en,
              chapters: t.chapters || 0,
              prefix: t.chapterPrefix || '',
              // for multi-file texts "file" is a placeholder ("index"), not a
              // name -- don't let it become something you can search for
              keys: (t.chapters ? [norm(t.en)] : [norm(t.file), norm(t.en)])
                .concat((t.alias || []).map(norm))
                .filter(Boolean)
            });
          });
        });
        return texts;
      })
      .catch(function () { texts = []; return texts; });
    return loading;
  }

  // ── query ────────────────────────────────────────────────────────────────

  /** Split "cha 7.25" into name + reference. */
  function parse(q) {
    var m = /^(.*?)[\s:]+([\d.]+)\s*$/.exec(q.trim());
    if (m) { return { name: m[1].trim(), ref: m[2].replace(/\.$/, '') }; }
    return { name: q.trim(), ref: '' };
  }

  function score(t, needle) {
    var best = -1;
    t.keys.forEach(function (k) {
      var s = -1;
      if (k === needle) { s = 100; }
      else if (k.indexOf(needle) === 0) { s = 70 - k.length; }
      else if (k.indexOf(needle) > 0) { s = 40 - k.length; }
      if (s > best) { best = s; }
    });
    return best;
  }

  function find(q) {
    var p = parse(q);
    var needle = norm(p.name);
    if (!needle) { return []; }
    return texts
      .map(function (t) { return { t: t, s: score(t, needle) }; })
      .filter(function (r) { return r.s >= 0; })
      .sort(function (a, b) { return b.s - a.s; })
      .slice(0, 8)
      .map(function (r) { return { text: r.t, ref: p.ref }; });
  }

  /** Where does this hit live, and what reference is left for the page? */
  function target(hit) {
    var t = hit.text, ref = hit.ref, file = t.file, rest = ref;
    if (t.chapters) {                     // gita / brahmasutra: first number picks the file
      file = t.prefix + 1;                // no chapter asked for -> start at the first
      if (ref) {
        var bits = ref.split('.');
        var n = parseInt(bits[0], 10);
        if (n >= 1 && n <= t.chapters) {
          file = t.prefix + n;
          rest = bits.slice(1).join('.');
        }
      }
    }
    var url = root + t.dir + '/' + file + '.html';
    return { url: url, ref: rest };
  }

  function go(hit) {
    var d = target(hit);
    var here = location.pathname.replace(/^.*\//, '');
    if (d.url.replace(/^.*\//, '') === here) {
      if (d.ref && !goToRef(d.ref)) { notFound(d.ref); }
      return;
    }
    location.href = d.url + (d.ref ? '#r=' + d.ref : '');
  }

  // ── ui ───────────────────────────────────────────────────────────────────

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) { e.className = cls; }
    if (text != null) { e.textContent = text; }
    return e;
  }

  function buildPanel(input, list) {
    var hits = [], cursor = 0;

    function draw() {
      list.innerHTML = '';
      cursor = 0;
      hits.forEach(function (h, i) {
        // the tier class carries the collection's colour into the row
        var row = el('div', 'search-row t-' + (h.text.tier || 'none') +
                            (i === 0 ? ' on' : ''));
        row.appendChild(el('span', 'search-name', h.text.en));
        row.appendChild(el('span', 'search-dev', h.text.dev));
        var tail = h.ref ? h.text.label + ' · ' + h.ref : h.text.label;
        row.appendChild(el('span', 'search-cat', tail));
        row.addEventListener('mouseenter', function () { move(i - cursor); });
        row.addEventListener('click', function () { pick(); });
        list.appendChild(row);
      });
      list.hidden = !hits.length;
    }

    function move(d) {
      var rows = list.querySelectorAll('.search-row');
      if (!rows.length) { return; }
      rows[cursor].classList.remove('on');
      cursor = (cursor + d + rows.length) % rows.length;
      rows[cursor].classList.add('on');
      rows[cursor].scrollIntoView({ block: 'nearest' });
    }

    function pick() {
      var h = hits[cursor];
      if (h) { go(h); }
    }

    function run() {
      var q = input.value;
      if (!q.trim()) { hits = []; draw(); return; }
      load().then(function () { hits = find(q); draw(); });
    }

    input.addEventListener('input', run);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') { e.preventDefault(); pick(); }
    });
    return run;
  }

  // ── overlay, opened with "/" ─────────────────────────────────────────────

  var overlay = null;

  function closeOverlay() {
    if (overlay) { overlay.hidden = true; }
  }

  function openOverlay() {
    if (!overlay) {
      overlay = el('div', 'search-overlay');
      overlay.hidden = true;
      var box = el('div', 'search-box');
      var input = el('input', 'search-input');
      input.type = 'text';
      input.setAttribute('aria-label', 'search texts');
      input.autocomplete = 'off';
      input.spellcheck = false;
      var list = el('div', 'search-list');
      list.hidden = true;
      box.appendChild(input);
      box.appendChild(list);
      overlay.appendChild(box);
      document.body.appendChild(overlay);
      buildPanel(input, list);
      overlay._input = input;

      overlay.addEventListener('click', function (e) {
        if (e.target === overlay) { closeOverlay(); }
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') { closeOverlay(); }
      });
    }
    overlay.hidden = false;
    load();
    overlay._input.focus();
    overlay._input.select();
  }

  // ── boot ─────────────────────────────────────────────────────────────────

  function boot() {
    // home page: a real input, not a shortcut
    // The input is in index.html, not created here -- injecting it after parse
    // made the page reflow on every visit to the home page.
    var home = document.querySelector('#search-home');
    if (home) {
      var input = home.querySelector('.search-input');
      var list = home.querySelector('.search-list');
      if (input && list) {
        buildPanel(input, list, false);
        load();
      }
    }

    // Only pages without the top-bar input need a button to reach search.
    if (!document.querySelector('.topbar .search-input')) {
      var bar = document.querySelector('.toolbar');
      if (bar) {
        var btn = el('button', 'search-open', '\u2315 Search');
        btn.type = 'button';
        btn.setAttribute('aria-label', 'search texts');
        btn.addEventListener('click', function () { openOverlay(); });
        bar.insertBefore(btn, bar.firstChild);
      }
    }

    document.addEventListener('keydown', function (e) {
      var t = e.target.tagName;
      if (t === 'INPUT' || t === 'TEXTAREA' || e.metaKey || e.ctrlKey) { return; }
      if (e.key === '/') { e.preventDefault(); openOverlay(); }
    });

    // arriving with #r=7.25
    var m = /^#r=([\d.]+)$/.exec(location.hash);
    if (m) {
      setTimeout(function () {
        if (!goToRef(m[1])) { notFound(m[1]); }
      }, 60);
    }
  }

  // Must run after script-toggle.js builds .toolbar. Its handler is registered
  // first, so DOMContentLoaded ordering sequences them -- but only if we wait.
  // readyState is 'interactive' at end of body, which is before that fires.
  if (document.readyState === 'complete') {
    setTimeout(boot, 0);
  } else {
    document.addEventListener('DOMContentLoaded', boot);
  }
})();
