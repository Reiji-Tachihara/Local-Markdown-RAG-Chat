import { FormEvent, useMemo, useState } from "react";
import styles from "./App.module.css";

type PersonaKey = "user_clone" | "rational_advisor";

type RagContext = {
  source_path: string;
  chunk_index: number;
  content: string;
  score: number;
};

type ChatResponse = {
  answer: string;
  persona: PersonaKey;
  generation_mode: string;
  contexts: RagContext[];
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  persona?: PersonaKey;
  contexts?: RagContext[];
};

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  ""
);

const personaLabels: Record<PersonaKey, string> = {
  user_clone: "ユーザーの分身",
  rational_advisor: "合理的な相談相手"
};

function App() {
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
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userContent,
          persona,
          top_k: 4
        })
      });

      if (!response.ok) {
        const detail = await readError(response);
        throw new Error(detail);
      }

      const data = (await response.json()) as ChatResponse;
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

  async function rebuildIndex() {
    setError(null);
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/index/rebuild`, {
        method: "POST"
      });
      if (!response.ok) {
        const detail = await readError(response);
        throw new Error(detail);
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "インデックス再構築に失敗しました。");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className={styles.shell}>
      <section className={styles.header}>
        <div>
          <p className={styles.kicker}>Local Markdown RAG</p>
          <h1>Markdown knowledge chat</h1>
          <p className={styles.summary}>
            ローカル Markdown を検索し、Ollama の回答に参照元を添えて表示します。
          </p>
        </div>
        <div className={styles.headerActions}>
          <span className={styles.apiUrl}>{API_BASE_URL}</span>
          <button className={styles.secondaryButton} onClick={rebuildIndex} disabled={isLoading}>
            Index rebuild
          </button>
        </div>
      </section>

      {error && <div className={styles.error}>{error}</div>}

      <section className={styles.layout}>
        <section className={styles.chatPanel} aria-label="チャット">
          <div className={styles.toolbar}>
            <label className={styles.field}>
              <span>Persona</span>
              <select
                value={persona}
                onChange={(event) => setPersona(event.target.value as PersonaKey)}
                disabled={isLoading}
              >
                <option value="user_clone">{personaLabels.user_clone}</option>
                <option value="rational_advisor">{personaLabels.rational_advisor}</option>
              </select>
            </label>
            <div className={styles.historyCount}>会話 {messageCount} 件</div>
          </div>

          <div className={styles.messages}>
            {messages.length === 0 ? (
              <div className={styles.emptyState}>
                Markdown 形式で相談内容を入力してください。回答には RAG 参照元が表示されます。
              </div>
            ) : (
              messages.map((message) => (
                <article key={message.id} className={`${styles.message} ${styles[message.role]}`}>
                  <div className={styles.messageMeta}>
                    <span>{message.role === "user" ? "You" : personaLabels[message.persona ?? persona]}</span>
                    {message.persona && <span>{message.persona}</span>}
                  </div>
                  <div className={styles.markdownText}>{message.content}</div>
                  {message.contexts && message.contexts.length > 0 && (
                    <ContextList contexts={message.contexts} compact />
                  )}
                </article>
              ))
            )}
            {isLoading && (
              <div className={styles.loading}>
                <span className={styles.spinner} />
                生成中です。Ollama の応答を待っています。
              </div>
            )}
          </div>

          <form className={styles.composer} onSubmit={submitChat}>
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={"Markdown で入力できます。\n例: ## 相談\nこの考えの飛躍を整理してほしい。"}
              rows={8}
              disabled={isLoading}
            />
            <div className={styles.composerFooter}>
              <span>Markdown input / Shift+Enter で改行</span>
              <button className={styles.primaryButton} type="submit" disabled={!canSend}>
                Send
              </button>
            </div>
          </form>
        </section>

        <aside className={styles.sidePanel} aria-label="RAG参照元">
          <div className={styles.sideHeader}>
            <h2>RAG references</h2>
            <p>直近の回答で参照された Markdown chunk です。</p>
          </div>
          {lastContexts.length > 0 ? (
            <ContextList contexts={lastContexts} />
          ) : (
            <div className={styles.emptyReference}>まだ参照元はありません。</div>
          )}
        </aside>
      </section>
    </main>
  );
}

function ContextList({ contexts, compact = false }: { contexts: RagContext[]; compact?: boolean }) {
  return (
    <div className={compact ? styles.compactContexts : styles.contextList}>
      {contexts.map((context) => (
        <details key={`${context.source_path}-${context.chunk_index}`} className={styles.contextItem}>
          <summary>
            <span>{context.source_path}</span>
            <span>chunk {context.chunk_index}</span>
            <span>{context.score.toFixed(3)}</span>
          </summary>
          <p>{context.content}</p>
        </details>
      ))}
    </div>
  );
}

async function readError(response: Response) {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") {
      return data.detail;
    }
    return JSON.stringify(data);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

export default App;
