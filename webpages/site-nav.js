const PAGE_REGISTRY = [
  { slug: 'cast', label: 'screen cast', href: '/cast' },
  { slug: 'remote', label: 'virtual remote', href: '/remote' },
];

function buildNav() {
  const currentPath = window.location.pathname;
  const navRoot = document.querySelector('[data-site-nav]');
  if (!navRoot) return;

  const nav = document.createElement('nav');
  nav.setAttribute('aria-label', 'Site navigation');

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
