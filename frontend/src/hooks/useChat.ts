import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { fetchHistory, rebuildIndex, sendChat } from "../api/client";
import type { ChatMessage, PersonaKey, RagContext } from "../types";

export function useChat() {
  const [persona, setPersona] = useState<PersonaKey>("rational_advisor");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastContexts, setLastContexts] = useState<RagContext[]>([]);

  const canSend = input.trim().length > 0 && !isLoading;
  const messageCount = useMemo(
    () => messages.filter((message) => message.role === "user").length,
    [messages]
  );

  const loadHistory = useCallback(async () => {
    setError(null);
    try {
      const data = await fetchHistory();
      const loadedMessages = data.messages
        .slice()
        .reverse()
        .map((message) => ({
          id: message.id,
          role: message.role,
          content: message.content,
          persona: message.persona,
          contexts: message.contexts
        }));

      setMessages(loadedMessages);
      const lastAssistant = loadedMessages
        .slice()
        .reverse()
        .find((message) => message.role === "assistant" && message.contexts?.length);
      setLastContexts(lastAssistant?.contexts ?? []);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "履歴の読み込みに失敗しました。");
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  async function submitChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSend) {
      return;
    }

    const userContent = input.trim();
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: userContent,
      persona
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setError(null);
    setIsLoading(true);

    try {
      const data = await sendChat(userContent, persona);
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
        persona: data.persona,
        contexts: data.contexts
      };
      setMessages((current) => [...current, assistantMessage]);
      setLastContexts(data.contexts);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "不明なエラーが発生しました。");
    } finally {
      setIsLoading(false);
    }
  }

  async function rebuildKnowledgeIndex() {
    setError(null);
    setIsLoading(true);
    try {
      await rebuildIndex();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "インデックス再構築に失敗しました。");
    } finally {
      setIsLoading(false);
    }
  }

  return {
    canSend,
    error,
    input,
    isLoading,
    lastContexts,
    loadHistory,
    messageCount,
    messages,
    persona,
    rebuildKnowledgeIndex,
    setInput,
    setPersona,
    submitChat
  };
}
