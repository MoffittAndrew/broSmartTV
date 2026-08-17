# Website structure

This folder defines the website conventions used by the TV app.

## Route model

The website is intentionally route-first instead of home-page-first.

- / redirects to /cast
- /cast is the main cast page
- /remote is the virtual remote page
- /standby is the dedicated standby page while the TV is powered down

The root page is not a landing page; it exists only as a redirect target so the browser always lands on the primary app page.

## Shared navigation

All main pages use the same shared navigation shell loaded from the static webpages directory.

- Pages should include a container such as a data-site-nav element
- The shared nav is built from a registry rather than by hardcoding page links in each HTML file
- Future pages should be added to the same registry rather than creating one-off links in a template

This keeps navigation consistent and makes CSS styling easy later without rewriting each page.

## Standby redirect flow

While the TV is in standby mode, the off-state server overrides the main pages and redirects them to /standby with a next target.

Example:

- /cast -> /standby?next=/cast
- /remote -> /standby?next=/remote

The standby page then powers the TV back on and sends the user back to the target page once the app server is active again. This keeps the flow centralized and avoids repeating redirect logic across every page.

## Static assets

The HTML, JS, and CSS assets now live in the webpages directory.

The Python webserver code must use this directory for static routing and for all page file responses. This keeps the site content and route logic in a single obvious location.

## Adding future pages

To add a new main page:

1. Add the page file under the webpages directory.
2. Add a matching item to the page registry in the shared nav script.
3. Add the route in the server to serve the page while the TV is on.
4. If the page should be blocked while the TV is off, rely on the shared standby redirect mechanism rather than a page-specific workaround.

This makes future expansion simple and keeps the website structure predictable for future work.
