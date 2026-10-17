/**
 * API configuration.
 * When running in single-origin mode (FastAPI serving frontend/dist on port 7860)
 * or proxied Vite dev server (port 3000), API_BASE is empty string ""
 * so all requests use relative paths seamlessly without hardcoded hostnames.
 */
export const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Returns a normalized asset URL ensuring correct prefixing with API_BASE if needed.
 */
export function getAssetUrl(url: string | null | undefined, fallback: string = ''): string {
  if (!url) return fallback;
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url;
  }
  const cleanPath = url.startsWith('/') ? url : `/${url}`;
  return `${API_BASE}${cleanPath}`;
}
