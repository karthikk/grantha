/**
 * Mobile sidebar: floating button at bottom-right, menu opens upward.
 */
(function() {
  if (window.innerWidth > 768) return;

  var sidebar = document.querySelector('.sidebar > nav');
  if (!sidebar) return;

  var ul = sidebar.querySelector(':scope > ul');
  if (!ul) return;

  var toggle = document.createElement('span');
  toggle.className = 'mobile-toggle';
  toggle.textContent = 'विषयसूची ▴';

  // Place toggle after the ul so it appears below (visually at bottom since it floats right)
  sidebar.appendChild(toggle);

  toggle.addEventListener('click', function() {
    ul.classList.toggle('mobile-open');
    toggle.textContent = ul.classList.contains('mobile-open') ? 'विषयसूची ✕' : 'विषयसूची ▴';
  });

  // Close menu when a link is clicked
  ul.querySelectorAll('a').forEach(function(a) {
    a.addEventListener('click', function() {
      ul.classList.remove('mobile-open');
      toggle.textContent = 'विषयसूची ▴';
    });
  });
})();
