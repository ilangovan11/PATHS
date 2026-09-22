export default function State({ label = "Loading...", compact = false }) {
  return (
    <div className={compact ? "state state--compact" : "state"}>
      <div className="spinner" role="status" aria-label="Loading" />
      <span>{label}</span>
    </div>
  );
}