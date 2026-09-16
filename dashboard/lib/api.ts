import type { Deployment, EAEvent, EAStatusResponse } from "./types";

const EA_ID = "AI_BASKET_EA";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/platform${path}`, {
    ...options,

    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },

    cache: "no-store",
  });

  if (!response.ok) {
    let message = `API request failed (${response.status})`;

    try {
      const body = (await response.json()) as {
        detail?: string;
      };

      if (typeof body.detail === "string") {
        message = body.detail;
      }
    } catch {
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function getEA(): Promise<EAStatusResponse> {
  return request(`/api/eas/${EA_ID}`);
}

export async function executeEAAction(
  action: "start" | "pause" | "resume" | "stop" | "close-basket",
): Promise<unknown> {
  return request(`/api/eas/${EA_ID}/${action}`, {
    method: "POST",
  });
}

export async function getEAEvents(): Promise<{
  ea_id: string;
  events: EAEvent[];
}> {
  return request(`/api/eas/${EA_ID}/events`);
}

export async function getDeployments(): Promise<{
  ea_id: string;
  deployments: Deployment[];
}> {
  return request(`/api/eas/${EA_ID}/deployments`);
}
