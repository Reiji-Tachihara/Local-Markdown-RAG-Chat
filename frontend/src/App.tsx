import { API_BASE_URL } from "./api/client";
import styles from "./App.module.css";
import { ChatPanel } from "./components/ChatPanel";
import { ReferencePanel } from "./components/ReferencePanel";
import { useChat } from "./hooks/useChat";

function App() {
  const chat = useChat();

  return (
    <main className={styles.shell}>
      <section className={styles.header}>
        <div>
          <p className={styles.kicker}>Local Markdown RAG</p>
          <h1>Markdown knowledge chat</h1>
          <p className={styles.summary}>
            ローカルの Markdown を検索し、Ollama の回答に参照元を添えて表示する RAG チャットです。
          </p>
        </div>
        <div className={styles.headerActions}>
          <span className={styles.apiUrl}>{API_BASE_URL}</span>
          <button className={styles.secondaryButton} onClick={chat.loadHistory} disabled={chat.isLoading}>
            Reload history
          </button>
          <button
            className={styles.secondaryButton}
            onClick={chat.rebuildKnowledgeIndex}
            disabled={chat.isLoading}
          >
            Index rebuild
          </button>
        </div>
      </section>

      {chat.error && <div className={styles.error}>{chat.error}</div>}

      <section className={styles.layout}>
        <ChatPanel
          canSend={chat.canSend}
          input={chat.input}
          isLoading={chat.isLoading}
          isTooLong={chat.isTooLong}
          messageCount={chat.messageCount}
          messages={chat.messages}
          persona={chat.persona}
          setInput={chat.setInput}
          setPersona={chat.setPersona}
          submitChat={chat.submitChat}
        />
        <ReferencePanel contexts={chat.lastContexts} />
      </section>
    </main>
  );
}

export default App;
