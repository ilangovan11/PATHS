/**
 * Donut chart built with a conic-gradient background. No chart library.
 */
export default function DonutChart({ segments, centerValue, centerLabel }) {
  const total = segments.reduce((sum, s) => sum + (s.value || 0), 0);
  if (total <= 0) {
    return null;
  }

  const positive = segments.filter((s) => s.value > 0);
  const stops = positive
    .reduce((acc, s) => {
      const from = acc.length ? acc[acc.length - 1].to : 0;
      return [...acc, { s, from, to: from + s.value }];
    }, [])
    .map(({ s, from, to }) => `${s.color} ${(from / total) * 100}% ${(to / total) * 100}%`)
    .join(", ");

  return (
    <div className="donut" style={{ background: `conic-gradient(${stops})` }} role="img" aria-label={centerLabel}>
      <div className="donut__center">
        <span className="donut__value">{centerValue}</span>
        <span className="donut__label">{centerLabel}</span>
      </div>
    </div>
  );
}