/**
 * Horizontal bar list: label, track, value. Colour optional per row.
 */
export default function BarChart({ items, color = "var(--primary)", valueFormatter = (v) => v }) {
  const max = Math.max(1, ...items.map((i) => i.value));
  return (
    <div className="bar-chart">
      {items.map((row) => (
        <div className="bar-row" key={row.label}>
          <span className="bar-row__label" title={row.label}>
            {row.label}
          </span>
          <div className="bar-row__track">
            <div
              className="bar-row__fill"
              style={{
                width: `${(row.value / max) * 100}%`,
                background: row.color || color,
              }}
            />
          </div>
          <span className="bar-row__value">{valueFormatter(row.value)}</span>
        </div>
      ))}
    </div>
  );
}