export type PersonaKey = "user_clone" | "rational_advisor";

export type RagContext = {
  source_path: string;
  chunk_index: number;
  content: string;
  score: number;
};

export type ChatMessage = {
  id: string | number;
  role: "user" | "assistant";
  content: string;
  persona?: PersonaKey;
  contexts?: RagContext[];
};

export type ChatResponse = {
  answer: string;
  persona: PersonaKey;
  generation_mode: string;
  contexts: RagContext[];
};

export type HistoryResponse = {
  messages: Array<{
    id: number;
    role: "user" | "assistant";
    content: string;
    persona: PersonaKey;
    contexts: RagContext[];
    created_at: string;
  }>;
};
