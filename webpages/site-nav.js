const PAGE_REGISTRY = [
  { slug: 'cast', label: 'screen cast', href: '/cast' },
  { slug: 'remote', label: 'virtual remote', href: '/remote' },
  { slug: 'logs', label: 'logs', href: '/logs' },
  { slug: 'webdebug', label: 'web debug', href: '/webdebug' },
];

function buildNav() {
  const currentPath = window.location.pathname;
  const navRoot = document.querySelector('[data-site-nav]');
  if (!navRoot) return;

  const nav = document.createElement('nav');
  nav.setAttribute('aria-label', 'Site navigation');
  nav.style.display = 'flex';
  nav.style.gap = '1.5rem';
  nav.style.padding = '0.5rem 1rem';

  PAGE_REGISTRY.forEach((page) => {
    const link = document.createElement('a');
    link.href = page.href;
    link.textContent = page.label;
    if (currentPath === page.href || (currentPath === '/' && page.slug === 'cast')) {
      link.setAttribute('aria-current', 'page');
    }
    nav.appendChild(link);
  });

  navRoot.replaceChildren(nav);
}

buildNav();
