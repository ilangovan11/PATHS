export default function EmptyState({ message, compact = false }) {
  return (
    <div className={compact ? "state state--compact" : "state"}>
      <span aria-hidden="true" style={{ fontSize: 26 }}>
        —
      </span>
      <span>{message}</span>
    </div>
  );
}