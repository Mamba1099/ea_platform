import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";

const PLATFORM_API_URL =
  process.env.PLATFORM_API_URL || "http://127.0.0.1:8000";

async function proxyRequest(request: Request, path: string[]) {
  const session = await getServerSession(authOptions);

  if (!session?.user || session.user.role !== "ADMIN") {
    return Response.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const targetPath = `/${path.join("/")}`;

  const incomingUrl = new URL(request.url);

  const targetUrl = new URL(
    targetPath,
    PLATFORM_API_URL.endsWith("/") ? PLATFORM_API_URL : `${PLATFORM_API_URL}/`,
  );

  incomingUrl.searchParams.forEach((value, key) => {
    targetUrl.searchParams.set(key, value);
  });

  const headers = new Headers(request.headers);

  headers.set("x-dashboard-user-id", session.user.id);
  headers.set("x-dashboard-user-role", session.user.role);

  headers.delete("host");

  const method = request.method.toUpperCase();

  const body =
    method === "GET" || method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const response = await fetch(targetUrl.toString(), {
    method,
    headers,
    body,
    cache: "no-store",
  });

  const responseHeaders = new Headers(response.headers);

  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });
}

export async function GET(
  request: Request,
  context: {
    params: Promise<{ path: string[] }>;
  },
) {
  const { path } = await context.params;

  return proxyRequest(request, path);
}

export async function POST(
  request: Request,
  context: {
    params: Promise<{ path: string[] }>;
  },
) {
  const { path } = await context.params;

  return proxyRequest(request, path);
}

export async function PUT(
  request: Request,
  context: {
    params: Promise<{ path: string[] }>;
  },
) {
  const { path } = await context.params;

  return proxyRequest(request, path);
}

export async function PATCH(
  request: Request,
  context: {
    params: Promise<{ path: string[] }>;
  },
) {
  const { path } = await context.params;

  return proxyRequest(request, path);
}

export async function DELETE(
  request: Request,
  context: {
    params: Promise<{ path: string[] }>;
  },
) {
  const { path } = await context.params;

  return proxyRequest(request, path);
}
