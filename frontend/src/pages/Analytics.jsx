import { useApi } from "../hooks/useApi";
import api from "../api/client";
import State from "../components/Loading";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import DonutChart from "../components/DonutChart";
import Badge from "../components/Badge";
import { ACTION_TONES, ACTION_COLORS } from "../constants";

const COLORS = ACTION_COLORS;

function formatTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

export default function Analytics() {
  const { data, loading, error, reload } = useApi(() =>
    Promise.all([
      api.get("/analytics/summary"),
      api.get("/analytics/confidence"),
      api.get("/analytics/stress-impact"),
      api.get("/analytics/recent?limit=10"),
    ]).then(([summary, confidence, stress, recent]) => ({
      data: {
        summary: summary.data,
        confidence: confidence.data,
        stress: stress.data,
        recent: recent.data,
      },
    }))
  );

  if (loading) {
    return <State label="Loading analytics..." />;
  }

  if (error) {
    return <ErrorBanner message={`Unable to load analytics. ${error}`} onDismiss={reload} />;
  }

  const { summary, confidence, stress, recent } = data;
  const total = summary?.total_decisions || 0;
  const distribution = [
    { label: "ADVANCE", value: summary?.advance || 0, color: COLORS.ADVANCE },
    { label: "HOLD", value: summary?.hold || 0, color: COLORS.HOLD },
    { label: "RETREAT", value: summary?.retreat || 0, color: COLORS.RETREAT },
  ];

  const stressRows = stress
    ? Object.entries(stress)
        .map(([level, actions]) => ({
          level: Number(level),
          actions: Object.entries(actions).map(([action, count]) => ({
            action,
            count,
            color: COLORS[action] || "var(--text-faint)",
          })),
        }))
        .sort((a, b) => a.level - b.level)
    : [];

  return (
    <>
      <div className="page-header">
        <h1 className="page-header__title">Analytics</h1>
        <p className="page-header__desc">
          Aggregate statistics computed from your recorded decisions.
        </p>
      </div>

      {total === 0 ? (
        <div className="card">
          <EmptyState message="No decisions have been recorded yet. Run a coordinate analysis first." />
        </div>
      ) : (
        <>
          <div className="stat-grid">
            <div className="stat">
              <div className="stat__label">Total Decisions</div>
              <div className="stat__value">{total}</div>
            </div>
            <div className="stat">
              <div className="stat__label">Avg Confidence</div>
              <div className="stat__value">
                {confidence?.average_confidence != null
                  ? (confidence.average_confidence * 100).toFixed(0) + "%"
                  : "—"}
              </div>
            </div>
            <div className="stat">
              <div className="stat__label">Max Confidence</div>
              <div className="stat__value">
                {confidence?.max_confidence != null
                  ? (confidence.max_confidence * 100).toFixed(0) + "%"
                  : "—"}
              </div>
            </div>
            <div className="stat">
              <div className="stat__label">Min Confidence</div>
              <div className="stat__value">
                {confidence?.min_confidence != null
                  ? (confidence.min_confidence * 100).toFixed(0) + "%"
                  : "—"}
              </div>
            </div>
          </div>

          <div className="card-row grid-2">
            <div className="card" style={{ margin: 0 }}>
              <h3 className="card__title">Decision distribution</h3>
              <p className="card__sub">Classification decisions made so far</p>
              <div style={{ display: "flex", gap: 28, alignItems: "center", flexWrap: "wrap" }}>
                <DonutChart segments={distribution} centerValue={total} centerLabel="decisions" />
                <div className="chart-legend">
                  {distribution.map((s) => (
                    <div className="legend-item" key={s.label}>
                      <span className="legend-dot" style={{ background: s.color }} />
                      <span className="legend-item__label">{s.label}</span>
                      <span className="legend-item__value">{s.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="card" style={{ margin: 0 }}>
              <h3 className="card__title">Stress impact</h3>
              <p className="card__sub">Decisions per reported stress level</p>
              {stressRows.length === 0 ? (
                <EmptyState compact message="No stress data recorded yet." />
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  {stressRows.map(({ level, actions }) => (
                    <div key={level}>
                      <div className="legend-item" style={{ marginBottom: 6 }}>
                        <span className="legend-item__label" style={{ fontWeight: 650 }}>
                          Stress level {level}
                        </span>
                      </div>
                      <div className="bar-row">
                        <span className="bar-row__label"> </span>
                        <div className="bar-row__track" style={{ display: "flex", overflow: "hidden" }}>
                          {actions.map((a) => (
                            <div
                              key={a.action}
                              title={`${a.action}: ${a.count}`}
                              style={{
                                width: `${(a.count / Math.max(1, actions.reduce((s, x) => s + x.count, 0))) * 100}%`,
                                background: a.color,
                                height: "100%",
                              }}
                            />
                          ))}
                        </div>
                        <span className="bar-row__value">
                          {actions.reduce((s, x) => s + x.count, 0)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <h3 className="card__title">Recent decisions</h3>
            <p className="card__sub">Latest 10 records</p>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Time</th>
                    <th>Decision</th>
                    <th>Prediction</th>
                    <th>Confidence</th>
                    <th>Reason</th>
                    <th>Model</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((r) => (
                    <tr key={r.id}>
                      <td className="table__muted">{r.id}</td>
                      <td className="table__muted">
                        <span style={{ whiteSpace: "nowrap" }}>{formatTime(r.created_at)}</span>
                      </td>
                      <td>
                        <Badge tone={ACTION_TONES[r.action] || "neutral"}>{r.action}</Badge>
                      </td>
                      <td>{r.prediction}</td>
                      <td className="table__mono">
                        {r.confidence != null ? (r.confidence * 100).toFixed(0) + "%" : "—"}
                      </td>
                      <td className="table__muted" style={{ maxWidth: 260 }}>
                        {r.reason}
                      </td>
                      <td className="table__mono">{r.model_version}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </>
  );
}