import type { ChatResponse, HistoryResponse, PersonaKey } from "../types";

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  ""
);

export async function sendChat(message: string, persona: PersonaKey, topK = 4): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      persona,
      top_k: topK
    })
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as ChatResponse;
}

export async function rebuildIndex(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/index/rebuild`, {
    method: "POST"
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }
}

export async function fetchHistory(limit = 80): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/history?limit=${limit}`);

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as HistoryResponse;
}

async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data.detail)) {
      return (data.detail as unknown[])
        .map((item) => {
          if (typeof item === "object" && item !== null && "msg" in item && typeof item.msg === "string") {
            return item.msg;
          }
          return JSON.stringify(item);
        })
        .join("\n");
    }
    return JSON.stringify(data);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}
