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

export default function Dashboard() {
  const { data, loading, error, reload } = useApi(() =>
    Promise.all([
      api.get("/analytics/summary"),
      api.get("/analytics/confidence"),
      api.get("/analytics/recent?limit=8"),
      api.get("/model/status"),
    ]).then(([summary, confidence, recent, model]) => ({
      data: {
        summary: summary.data,
        confidence: confidence.data,
        recent: recent.data,
        model: model.data,
      },
    }))
  );

  if (loading) {
    return <State label="Loading dashboard..." />;
  }

  if (error) {
    return <ErrorBanner message={`Unable to load analytics. ${error}`} onDismiss={reload} />;
  }

  const { summary, confidence, recent, model } = data;
  const total = summary?.total_decisions || 0;
  const distribution = [
    { label: "ADVANCE", value: summary?.advance || 0, color: COLORS.ADVANCE },
    { label: "HOLD", value: summary?.hold || 0, color: COLORS.HOLD },
    { label: "RETREAT", value: summary?.retreat || 0, color: COLORS.RETREAT },
  ];
  const avgConf = confidence?.average_confidence;

  return (
    <>
      <div className="page-header">
        <h1 className="page-header__title">Dashboard</h1>
        <p className="page-header__desc">
          Live decision activity and serving-model status.
        </p>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="kv">
          <span className="kv__k">Active model</span>
          <span className="kv__v">
            {model?.active_model || "none"} · {model?.model_type || "?"}
          </span>
          <span className="kv__k">Trained at</span>
          <span className="kv__v">{formatTime(model?.trained_at)}</span>
          <span className="kv__k">Accuracy</span>
          <span className="kv__v">{model?.metrics?.accuracy != null ? (model.metrics.accuracy * 100).toFixed(1) + "%" : "—"}</span>
          <span className="kv__k">Macro F1</span>
          <span className="kv__v">{model?.metrics?.f1_macro != null ? model.metrics.f1_macro.toFixed(3) : "—"}</span>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat">
          <div className="stat__label">Total Decisions</div>
          <div className="stat__value">{total}</div>
          <div className="stat__hint">recorded in database</div>
        </div>
        <div className="stat">
          <div className="stat__label">Average Confidence</div>
          <div className="stat__value">{avgConf != null ? (avgConf * 100).toFixed(0) + "%" : "—"}</div>
          <div className="stat__hint">model confidence, not calibrated</div>
        </div>
        <div className="stat">
          <div className="stat__label">ADVANCE</div>
          <div className="stat__value" style={{ color: COLORS.ADVANCE }}>
            {summary?.advance || 0}
          </div>
          <div className="stat__hint">stable performance</div>
        </div>
        <div className="stat">
          <div className="stat__label">RETREAT</div>
          <div className="stat__value" style={{ color: COLORS.RETREAT }}>
            {summary?.retreat || 0}
          </div>
          <div className="stat__hint">needs intervention</div>
        </div>
      </div>

      <div className="card-row grid-2">
        <div className="card" style={{ margin: 0 }}>
          <h3 className="card__title">Decision distribution</h3>
          <p className="card__sub">All recorded decisions</p>
          {total === 0 ? (
            <EmptyState compact message="No decisions have been recorded yet." />
          ) : (
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
                <div className="legend-item" style={{ marginTop: 4 }}>
                  <span className="legend-dot" style={{ background: "var(--warn)" }} />
                  <span className="legend-item__label">HOLD</span>
                  <span className="legend-item__value">{summary?.hold || 0}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="card" style={{ margin: 0 }}>
          <h3 className="card__title">Recent decisions</h3>
          <p className="card__sub">Latest records from the decision log</p>
          {recent?.length ? (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Decision</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.slice(0, 6).map((r) => (
                    <tr key={r.id}>
                      <td className="table__muted">
                        <span style={{ whiteSpace: "nowrap" }}>{formatTime(r.created_at)}</span>
                      </td>
                      <td>
                        <Badge tone={ACTION_TONES[r.action] || "neutral"}>{r.action}</Badge>
                      </td>
                      <td className="table__mono">
                        {r.confidence != null ? (r.confidence * 100).toFixed(0) + "%" : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState compact message="No decisions have been recorded yet." />
          )}
        </div>
      </div>
    </>
  );
}