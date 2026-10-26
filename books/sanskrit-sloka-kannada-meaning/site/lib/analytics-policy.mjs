// Collect page views only; never forward search terms, fragment IDs or custom data.
export function pageviewOnly(event) {
  if (event.type !== 'pageview') return null;
  try {
    const url = new URL(event.url);
    if (!['http:', 'https:'].includes(url.protocol)) return null;
    url.search = '';
    url.hash = '';
    url.username = '';
    url.password = '';
    return { type: 'pageview', url: url.toString() };
  } catch {
    return null;
  }
}
