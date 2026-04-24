/**
 * Mobile sidebar: collapse to a toggle button.
 */
(function() {
  if (window.innerWidth > 768) return;

  var sidebar = document.querySelector('.sidebar > nav');
  if (!sidebar) return;

  var ul = sidebar.querySelector(':scope > ul');
  if (!ul) return;

  var toggle = document.createElement('span');
  toggle.className = 'mobile-toggle';
  toggle.textContent = 'विषयसूची ▾';
  sidebar.insertBefore(toggle, ul);

  toggle.addEventListener('click', function() {
    ul.classList.toggle('mobile-open');
    toggle.textContent = ul.classList.contains('mobile-open') ? 'विषयसूची ▴' : 'विषयसूची ▾';
  });
})();
