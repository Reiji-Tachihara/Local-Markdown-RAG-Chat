import styles from "../App.module.css";
import type { RagContext } from "../types";
import { ContextList } from "./ContextList";

type ReferencePanelProps = {
  contexts: RagContext[];
};

export function ReferencePanel({ contexts }: ReferencePanelProps) {
  return (
    <aside className={styles.sidePanel} aria-label="RAG references">
      <div className={styles.sideHeader}>
        <h2>RAG references</h2>
        <p>直近の回答で参照されたMarkdown chunkです。</p>
      </div>
      {contexts.length > 0 ? (
        <ContextList contexts={contexts} />
      ) : (
        <div className={styles.emptyReference}>まだ参照元はありません。</div>
      )}
    </aside>
  );
}
