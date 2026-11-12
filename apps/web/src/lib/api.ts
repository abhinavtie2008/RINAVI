const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  return parseResponse<T>(response);
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
