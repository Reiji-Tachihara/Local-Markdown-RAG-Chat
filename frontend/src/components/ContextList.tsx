import styles from "../App.module.css";
import type { RagContext } from "../types";

type ContextListProps = {
  contexts: RagContext[];
  compact?: boolean;
};

export function ContextList({ contexts, compact = false }: ContextListProps) {
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
