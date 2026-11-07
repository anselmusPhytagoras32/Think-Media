// FR01–02, FR11 / NFR02–03: same-origin HttpOnly session + session-bound CSRF.
export type Role = "student" | "instructor" | "company" | "administrator";
export type Profile = {
  kind: Role;
  institution?: string;
  program?: string;
  skills?: string[];
  interests?: string[];
  company_name?: string;
  description?: string;
  location?: string;
  website?: string | null;
  verification_status?: string;
  contact_email?: string | null;
  contact_phone?: string | null;
  background?: string;
  verification_version?: number;
};
export type Account = {
  user: {
    id: string;
    email: string;
    display_name: string;
    role: Role;
    created_at: string;
  };
  profile: Profile;
};
export type Company = {
  contact_email?: string | null;
  contact_phone?: string | null;
  id: string;
  company_name: string;
  description: string;
  location: string;
  website: string | null;
  verification_status: string;
  verification_version: number;
};
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public fields: Record<string, string[]> = {},
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {};
  if (method !== "GET") {
    const bootstrap = await fetch("/api/v1/auth/csrf", {
      credentials: "same-origin",
      cache: "no-store",
    });
    if (!bootstrap.ok)
      throw new ApiError(
        bootstrap.status,
        "Could not establish a secure session. Please try again.",
      );
    headers["X-CSRF-Token"] = (await bootstrap.json()).csrf_token;
    if (!(body instanceof FormData))
      headers["Content-Type"] = "application/json";
  }
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      method,
      headers,
      credentials: "same-origin",
      cache: "no-store",
      body:
        body === undefined
          ? undefined
          : body instanceof FormData
            ? body
            : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      0,
      "Cannot reach ThinkMedia. Check your connection and try again.",
    );
  }
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok)
    throw new ApiError(
      response.status,
      data?.error?.message || "The service is unavailable. Please try again.",
      data?.error?.fields,
    );
  return data as T;
}
export const manila = (value: string) =>
  new Intl.DateTimeFormat("en-PH", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Manila",
  }).format(new Date(value));
