/**
 * api/client.ts — Authenticated fetch wrapper for the RecallOS desktop API.
 *
 * Reads the per-session token from the URL query string (`?token=xxx`)
 * that pywebview injects at launch, and attaches it as an
 * `X-Session-Token` header on every `/api/*` request.
 */

const params = new URLSearchParams(window.location.search);
const SESSION_TOKEN = params.get("token") || "";

/**
 * Drop-in replacement for `fetch()` that adds the session-token header.
 */
export async function apiFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const headers = new Headers(init?.headers);
  if (SESSION_TOKEN) {
    headers.set("X-Session-Token", SESSION_TOKEN);
  }
  return fetch(path, { ...init, headers });
}

/**
 * Convenience: GET JSON from an API path.
 */
export async function apiGet<T = unknown>(path: string): Promise<T> {
  const res = await apiFetch(path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

/**
 * Convenience: POST JSON to an API path.
 */
export async function apiPost<T = unknown>(
  path: string,
  body: unknown,
): Promise<T> {
  const res = await apiFetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

/**
 * Convenience: PUT JSON to an API path.
 */
export async function apiPut<T = unknown>(
  path: string,
  body: unknown,
): Promise<T> {
  const res = await apiFetch(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}
