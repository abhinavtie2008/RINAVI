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

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new ApiError(response.status, `API request failed: ${response.status}`);
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
