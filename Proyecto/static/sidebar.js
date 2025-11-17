// Reemplazo: más robusto y con cierre al hacer click fuera (mobile)
document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebarToggle');
  const submenuButtons = Array.from(document.querySelectorAll('.submenu-toggle'));
  const storageKey = 'sidebarCollapsed';

  if (!sidebar || !toggle) return;

  // estado inicial
  const collapsed = localStorage.getItem(storageKey) === 'true';
  if (collapsed) sidebar.classList.add('is-collapsed');
  sidebar.setAttribute('aria-hidden', String(collapsed));

  // toggle principal
  toggle.addEventListener('click', (e) => {
    const isCollapsed = sidebar.classList.toggle('is-collapsed');
    const isOpenMobile = sidebar.classList.toggle('is-open', !isCollapsed && window.innerWidth <= 768 ? true : sidebar.classList.contains('is-open'));
    sidebar.setAttribute('aria-hidden', String(isCollapsed));
    toggle.setAttribute('aria-expanded', String(!isCollapsed));
    localStorage.setItem(storageKey, String(isCollapsed));
    // prevent accidental form focus
    e.stopPropagation();
  });

  // cerrar al clicar fuera (solo en mobile cuando abierto)
  document.addEventListener('click', (e) => {
    if (window.innerWidth > 768) return;
    if (!sidebar.classList.contains('is-open')) return;
    if (!sidebar.contains(e.target) && e.target !== toggle) {
      sidebar.classList.remove('is-open');
    }
  });

  // submenus
  submenuButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const parent = btn.closest('.has-sub');
      if (!parent) return;
      const submenu = parent.querySelector('.submenu');
      if (!submenu) return;
      submenu.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(submenu.classList.contains('open')));
    });
  });

  // cerrar con ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      sidebar.classList.remove('is-open');
    }
  });
});