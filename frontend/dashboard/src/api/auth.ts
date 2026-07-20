// Talks to supplier-service directly rather than through the GraphQL
// gateway — proxying a Set-Cookie response through a GraphQL mutation
// resolver isn't straightforward, and browsers share cookies by domain
// regardless of port, so a direct call works and the cookie still reaches
// the gateway (and every other service) on subsequent requests.
const SUPPLIER_SERVICE_URL = import.meta.env.VITE_SUPPLIER_SERVICE_URL ?? "http://localhost:5001";

export interface CurrentUser {
  id: number;
  email: string;
  role: string;
}

async function parseErrorOr<T>(response: Response): Promise<T> {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error ?? "request failed");
  }
  return body;
}

export async function login(email: string, password: string): Promise<CurrentUser> {
  const response = await fetch(`${SUPPLIER_SERVICE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  return parseErrorOr<CurrentUser>(response);
}

export async function logout(): Promise<void> {
  await fetch(`${SUPPLIER_SERVICE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}
