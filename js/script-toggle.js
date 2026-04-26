/**
 * Script toggle: Devanagari / Tamil / IAST
 * Uses Aksharamukha REST API for transliteration.
 * Stores preference in localStorage.
 */

(function() {
  var API = 'https://aksharamukha.appspot.com/api/public';
  var SCRIPTS = {
    'Devanagari': 'दे',
    'Tamil': 'த',
    'IAST': 'ia'
  };
  var current = localStorage.getItem('grantha-script') || 'Devanagari';
  var cache = {}; // cache[elementId][script] = text

  function buildToggle() {
    var bar = document.createElement('div');
    bar.className = 'script-toggle';

    Object.keys(SCRIPTS).forEach(function(script) {
      var btn = document.createElement('a');
      btn.href = '#';
      btn.className = 'script-btn' + (script === current ? ' active' : '');
      btn.textContent = SCRIPTS[script];
      btn.setAttribute('data-script', script);
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        switchScript(script);
        document.querySelectorAll('.script-btn').forEach(function(b) {
          b.classList.toggle('active', b.getAttribute('data-script') === script);
        });
      });
      bar.appendChild(btn);
    });

    // Insert into toolbar (create if needed), after h1
    var h1 = document.querySelector('h1');
    if (h1) {
      var toolbar = h1.parentNode.querySelector('.toolbar');
      if (!toolbar) {
        toolbar = document.createElement('div');
        toolbar.className = 'toolbar';
        // Move playlist-links into toolbar if present
        var pl = h1.parentNode.querySelector('.playlist-links');
        if (pl) {
          h1.parentNode.insertBefore(toolbar, pl);
          toolbar.appendChild(bar);
          toolbar.appendChild(pl);
        } else {
          h1.parentNode.insertBefore(toolbar, h1.nextSibling);
          toolbar.appendChild(bar);
        }
      } else {
        toolbar.insertBefore(bar, toolbar.firstChild);
      }
    }
  }

  function getShlokaElements() {
    return document.querySelectorAll('.shloka');
  }

  function storeOriginals() {
    var els = getShlokaElements();
    els.forEach(function(el, i) {
      var id = 'shloka-' + i;
      el.setAttribute('data-shloka-id', id);
      if (!cache[id]) cache[id] = {};
      cache[id]['Devanagari'] = el.innerHTML;
    });
  }

  function switchScript(target) {
    current = target;
    localStorage.setItem('grantha-script', target);

    if (target === 'Devanagari') {
      // Restore originals
      getShlokaElements().forEach(function(el) {
        var id = el.getAttribute('data-shloka-id');
        if (cache[id] && cache[id]['Devanagari']) {
          el.innerHTML = cache[id]['Devanagari'];
        }
      });
      return;
    }

    // Transliterate each shloka
    getShlokaElements().forEach(function(el) {
      var id = el.getAttribute('data-shloka-id');

      // Check cache
      if (cache[id] && cache[id][target]) {
        el.innerHTML = cache[id][target];
        return;
      }

      // Extract text, preserving HTML structure
      var original = cache[id]['Devanagari'];
      // Get just the text nodes to transliterate
      var textContent = el.textContent;

      var url = API + '?source=Devanagari&target=' + encodeURIComponent(target) +
                '&text=' + encodeURIComponent(textContent);

      fetch(url)
        .then(function(r) { return r.text(); })
        .then(function(converted) {
          // Rebuild HTML: replace text but keep <br> and <span> structure
          var html = original;
          // Get original text segments (split by HTML tags)
          var origTexts = original.split(/<[^>]+>/);
          var convTexts = converted.split(/\n/);

          // Simple approach: replace the innerHTML with converted text,
          // re-inserting <br> for line breaks and preserving verse-num spans
          var verseNum = '';
          var numMatch = original.match(/<span class="verse-num">.*?<\/span>/);
          if (numMatch) {
            verseNum = numMatch[0];
          }

          // Remove verse-num from converted text if it got included
          var cleanConverted = converted.replace(/॥[^॥]*॥/g, '').trim();
          // For IAST, the double dandas might be converted too
          cleanConverted = cleanConverted.replace(/\|\|[^|]*\|\|/g, '').trim();

          var lines = cleanConverted.split('\n').filter(function(l) { return l.trim(); });
          var newHtml = '\n      ' + lines.join('<br>\n      ');
          if (verseNum) {
            newHtml += ' ' + verseNum;
          }

          if (!cache[id]) cache[id] = {};
          cache[id][target] = newHtml;
          el.innerHTML = newHtml;
        })
        .catch(function(err) {
          console.error('Transliteration failed:', err);
        });
    });
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', function() {
    // Only add toggle on pages with shlokas
    if (!document.querySelector('.shloka')) return;

    storeOriginals();
    buildToggle();

    // Apply stored preference
    if (current !== 'Devanagari') {
      switchScript(current);
    }
  });
})();
