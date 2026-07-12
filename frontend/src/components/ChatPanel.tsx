import styles from "../App.module.css";
import { personaLabels } from "../constants";
import type { ChatMessage, PersonaKey } from "../types";
import { ContextList } from "./ContextList";

type ChatPanelProps = {
  canSend: boolean;
  input: string;
  isLoading: boolean;
  messageCount: number;
  messages: ChatMessage[];
  persona: PersonaKey;
  setInput: (value: string) => void;
  setPersona: (value: PersonaKey) => void;
  submitChat: (event: React.FormEvent<HTMLFormElement>) => void;
};

export function ChatPanel({
  canSend,
  input,
  isLoading,
  messageCount,
  messages,
  persona,
  setInput,
  setPersona,
  submitChat
}: ChatPanelProps) {
  return (
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
            Markdownの知識ベースについて質問できます。回答には参照されたRAGコンテキストが表示されます。
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
            生成中です。Ollamaの応答を待っています。
          </div>
        )}
      </div>

      <form className={styles.composer} onSubmit={submitChat}>
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={"Markdownで質問を入力できます。\n例: この知識ベースの要点をまとめて"}
          rows={8}
          disabled={isLoading}
        />
        <div className={styles.composerFooter}>
          <span>Markdown input / Shift+Enterで改行</span>
          <button className={styles.primaryButton} type="submit" disabled={!canSend}>
            Send
          </button>
        </div>
      </form>
    </section>
  );
}
