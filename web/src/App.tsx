import { FormEvent, useEffect, useMemo, useState } from "react";
import styles from "./App.module.css";

type PersonaKey = "user_clone" | "rational_advisor";

// FastAPI の /api/chat が返す RAG 参照元1件分の型。
type RagContext = {
  source_path: string;
  chunk_index: number;
  content: string;
  score: number;
};

// FastAPI の /api/chat のレスポンス型。
type ChatResponse = {
  answer: string;
  persona: PersonaKey;
  generation_mode: string;
  contexts: RagContext[];
};

// 画面上に表示する会話メッセージの型。
type ChatMessage = {
  id: string | number;
  role: "user" | "assistant";
  content: string;
  persona?: PersonaKey;
  contexts?: RagContext[];
};

type HistoryResponse = {
  messages: Array<{
    id: number;
    role: "user" | "assistant";
    content: string;
    persona: PersonaKey;
    contexts: RagContext[];
    created_at: string;
  }>;
};

// Vite では VITE_ で始まる環境変数だけがブラウザ側に公開される。
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  ""
);

// UI 表示用のペルソナ名。API に送る値とは分けて管理する。
const personaLabels: Record<PersonaKey, string> = {
  user_clone: "ユーザー",
  rational_advisor: "相談相手"
};

function App() {
  // persona は次に送信するチャットで使うペルソナ。
  const [persona, setPersona] = useState<PersonaKey>("rational_advisor");
  // input は textarea に入力中の Markdown テキスト。
  const [input, setInput] = useState("");
  // messages は画面に表示する会話履歴。ブラウザをリロードすると消える一時的な履歴。
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  // isLoading は API 呼び出し中の二重送信防止とローディング表示に使う。
  const [isLoading, setIsLoading] = useState(false);
  // error は API エラーやネットワークエラーを画面に出すための文字列。
  const [error, setError] = useState<string | null>(null);
  // lastContexts は右側の RAG references に表示する直近回答の参照元。
  const [lastContexts, setLastContexts] = useState<RagContext[]>([]);

  // 空入力や API 呼び出し中は送信ボタンを無効化する。
  const canSend = input.trim().length > 0 && !isLoading;

  useEffect(() => {
    // 画面を開いた時に、SQLite に保存済みのチャット履歴を読み込む。
    loadHistory();
  }, []);

  // ユーザーが送った回数だけを会話件数として表示する。
  const messageCount = useMemo(
    () => messages.filter((message) => message.role === "user").length,
    [messages]
  );

  async function submitChat(event: FormEvent<HTMLFormElement>) {
    // form の標準送信でページ全体が再読み込みされないようにする。
    event.preventDefault();
    if (!canSend) {
      return;
    }

    // userContent は API に送る確定済み入力。前後の空白はここで落とす。
    const userContent = input.trim();
    // userMessage は、API の応答を待つ前に画面へ即時追加するユーザー発言。
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
      // FastAPI の RAG チャット API を呼び出す。
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
      // assistantMessage は Ollama が生成した回答と、その回答に使った参照元を持つ。
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
      // fetch 失敗、FastAPI の 503、Ollama 未起動などをここで画面表示用に変換する。
      setError(caughtError instanceof Error ? caughtError.message : "不明なエラーが発生しました。");
    } finally {
      setIsLoading(false);
    }
  }

  async function rebuildIndex() {
    // Markdown を追加・編集した後に、検索用 DB を作り直すための処理。
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

  async function loadHistory() {
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/history?limit=80`);
      if (!response.ok) {
        const detail = await readError(response);
        throw new Error(detail);
      }
      const data = (await response.json()) as HistoryResponse;
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
          <button className={styles.secondaryButton} onClick={loadHistory} disabled={isLoading}>
            Reload history
          </button>
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
  // compact=true はチャット本文下の小さい参照元表示、false は右ペイン用。
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
  // FastAPI は { detail: "..."} でエラーを返すため、まず JSON として読む。
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
