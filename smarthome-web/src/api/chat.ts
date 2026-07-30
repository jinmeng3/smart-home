import { createApiHeaders, parseResponse } from "./client";

export interface ChatCompletionMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

interface StreamPayload {
  error?: unknown;
  choices?: Array<{
    delta?: {
      content?: string;
    };
  }>;
}

const parseContentDelta = (line: string) => {
  if (!line.startsWith("data: ")) {
    return "";
  }

  const data = line.slice(6).trim();

  if (!data || data === "[DONE]") {
    return "";
  }

  const payload = JSON.parse(data) as StreamPayload;

  if (payload.error) {
    throw new Error(String(payload.error));
  }

  return payload.choices?.[0]?.delta?.content ?? "";
};

export const streamChatCompletion = async (
  messages: ChatCompletionMessage[],
  onDelta: (content: string) => void,
  signal: AbortSignal,
) => {
  const response = await fetch("/api/chat/completions", {
    method: "POST",
    headers: createApiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ messages, stream: true }),
    signal,
  });

  if (!response.ok || !response.body) {
    await parseResponse<never>(response);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const delta = parseContentDelta(line.trim());

        if (delta) {
          onDelta(delta);
        }
      }
    }
  } finally {
    if (signal.aborted) {
      await reader.cancel().catch(() => undefined);
    }
    reader.releaseLock();
  }
};
