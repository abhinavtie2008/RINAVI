const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 30_000;

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

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const timeoutController = new AbortController();
  const timer = setTimeout(
    () => timeoutController.abort(),
    REQUEST_TIMEOUT_MS,
  );
  try {
    const signal = init?.signal
      ? AbortSignal.any([init.signal, timeoutController.signal])
      : timeoutController.signal;
    const response = await fetch(`${API_URL}${path}`, {
      ...init,
      credentials: "include",
      signal,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
    return await parseResponse<T>(response);
  } finally {
    clearTimeout(timer);
  }
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  // No explicit Content-Type: the browser sets the multipart boundary.
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  return parseResponse<T>(response);
}
