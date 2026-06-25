import type { Comment } from "../types";
import styles from "./CommentThread.module.css";

interface Props {
  comments: Comment[];
}

export function CommentThread({ comments }: Props) {
  if (comments.length === 0) {
    return <div className={styles.empty}>No comments</div>;
  }

  const sorted = [...comments].sort(
    (a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );

  return (
    <div className={styles.thread}>
      {sorted.map((comment, index) => (
        <div key={index} className={styles.comment}>
          <div className={styles.header}>
            <span className={styles.author}>
              {comment.created_by ?? "Anonymous"}
            </span>
            <time className={styles.time} dateTime={comment.created_at}>
              {new Date(comment.created_at).toLocaleString()}
            </time>
          </div>
          <div className={styles.body}>{comment.body}</div>
        </div>
      ))}
    </div>
  );
}
