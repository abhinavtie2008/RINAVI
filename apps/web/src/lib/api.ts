const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 30_000;
// Uploads can legitimately take longer than JSON requests (10 MB body plus
// server-side extraction), but must still be bounded.
const UPLOAD_TIMEOUT_MS = 120_000;

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// FastAPI puts a human-readable reason in `detail`: a string for a deliberate
// refusal ("Active consent required for documents.processing") or an array of
// validation objects for a rejected body. The UI showed only "API request
// failed: 403" before, which told the citizen nothing they could act on.
function errorDetail(payload: unknown): string | null {
  if (typeof payload !== "object" || payload === null) return null;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string" && detail.trim() !== "") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((entry) =>
        typeof entry === "object" && entry !== null
          ? (entry as { msg?: unknown }).msg
          : undefined,
      )
      .filter((msg): msg is string => typeof msg === "string" && msg !== "");
    if (messages.length) return messages.join("; ");
  }
  return null;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    // The error body is the only place the reason lives, and it may not be
    // JSON at all (a proxy or an unexpected crash). Never fail while reading it.
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
    const detail = errorDetail(payload);
    throw new ApiError(
      response.status,
      detail ?? `API request failed: ${response.status}`,
    );
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function withTimeout(timeoutMs: number, callerSignal?: AbortSignal | null) {
  const timeoutController = new AbortController();
  const timer = setTimeout(() => timeoutController.abort(), timeoutMs);
  const signal = callerSignal
    ? AbortSignal.any([callerSignal, timeoutController.signal])
    : timeoutController.signal;
  return { signal, clear: () => clearTimeout(timer) };
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const timeout = withTimeout(REQUEST_TIMEOUT_MS, init?.signal);
  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...init,
      credentials: "include",
      signal: timeout.signal,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
    return await parseResponse<T>(response);
  } finally {
    timeout.clear();
  }
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const timeout = withTimeout(UPLOAD_TIMEOUT_MS);
  try {
    // No explicit Content-Type: the browser sets the multipart boundary.
    const response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      credentials: "include",
      body: formData,
      signal: timeout.signal,
    });
    return await parseResponse<T>(response);
  } finally {
    timeout.clear();
  }
}
