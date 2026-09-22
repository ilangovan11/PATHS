import { useApi } from "../hooks/useApi";
import api from "../api/client";
import State from "../components/Loading";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import BarChart from "../components/BarChart";

function formatTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

export default function ModelInsights() {
  const { data, loading, error, reload } = useApi(() => api.get("/model/status"));

  if (loading) {
    return <State label="Loading model insights..." />;
  }

  if (error) {
    return <ErrorBanner message={`Unable to load model status. ${error}`} onDismiss={reload} />;
  }

  if (!data || !data.active_model) {
    return (
      <div className="card">
        <EmptyState message="No trained model is registered. Run `python -m model.trainer` in the backend." />
      </div>
    );
  }

  const { active_model, model_type, trained_at, features, hyperparameters, class_names, metrics, dataset } = data;
  const perClass = metrics?.per_class || {};
  const classes = Object.keys(perClass).sort();

  return (
    <>
      <div className="page-header">
        <h1 className="page-header__title">Model Insights</h1>
        <p className="page-header__desc">
          Configuration, evaluation and global explainability of the active model.
        </p>
      </div>

      <div className="error-banner" style={{ background: "var(--info-bg)", color: "var(--info)" }}>
        Evaluation shown here is based on the synthetic development dataset. It
        does not represent real-world accuracy.
      </div>

      <div className="card-row grid-2">
        <div className="card" style={{ margin: 0 }}>
          <h3 className="card__title">Active model</h3>
          <div className="kv" style={{ marginTop: 10 }}>
            <span className="kv__k">Version</span>
            <span className="kv__v table__mono">{active_model}</span>
            <span className="kv__k">Type</span>
            <span className="kv__v">{model_type}</span>
            <span className="kv__k">Trained at</span>
            <span className="kv__v">{formatTime(trained_at)}</span>
            <span className="kv__k">Classes</span>
            <span className="kv__v">{Object.values(class_names || {}).join(" / ")}</span>
            <span className="kv__k">Train samples</span>
            <span className="kv__v">{dataset?.train_samples ?? "—"}</span>
            <span className="kv__k">Eval samples</span>
            <span className="kv__v">{dataset?.eval_samples ?? "—"}</span>
            <span className="kv__k">Data source</span>
            <span className="kv__v table__mono" style={{ fontWeight: 400 }}>
              {dataset?.description || dataset?.source || "—"}
            </span>
          </div>
        </div>

        <div className="card" style={{ margin: 0 }}>
          <h3 className="card__title">Input features</h3>
          <p className="card__sub">Explicit feature order shared by training and inference</p>
          <div className="pill-list">
            {(features || []).map((f) => (
              <span className="pill" key={f}>{f}</span>
            ))}
          </div>

          <h3 className="card__title" style={{ marginTop: 22 }}>
            Hyperparameters
          </h3>
          <div className="kv" style={{ marginTop: 10 }}>
            {Object.entries(hyperparameters || {})
              .filter(([k]) => !["n_jobs"].includes(k))
              .map(([key, value]) => (
                <div key={key} style={{ display: "contents" }}>
                  <span className="kv__k">{key}</span>
                  <span className="kv__v table__mono" style={{ fontWeight: 400 }}>
                    {String(value)}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>

      <div className="card-row grid-2">
        <div className="card" style={{ margin: 0 }}>
          <h3 className="card__title">Evaluation metrics</h3>
          <p className="card__sub">Held-out test set</p>
          <div className="table-wrap">
            <table className="table">
              <tbody>
                <tr>
                  <td>Accuracy</td>
                  <td className="table__mono">{metrics?.accuracy != null ? metrics.accuracy.toFixed(4) : "—"}</td>
                </tr>
                <tr>
                  <td>Precision (macro)</td>
                  <td className="table__mono">{metrics?.precision_macro != null ? metrics.precision_macro.toFixed(4) : "—"}</td>
                </tr>
                <tr>
                  <td>Recall (macro)</td>
                  <td className="table__mono">{metrics?.recall_macro != null ? metrics.recall_macro.toFixed(4) : "—"}</td>
                </tr>
                <tr>
                  <td>F1 (macro)</td>
                  <td className="table__mono">{metrics?.f1_macro != null ? metrics.f1_macro.toFixed(4) : "—"}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h3 className="card__title" style={{ marginTop: 20 }}>
            Per-class metrics
          </h3>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Class</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                  <th>Support</th>
                </tr>
              </thead>
              <tbody>
                {classes.map((cls) => {
                  const row = perClass[cls];
                  return (
                    <tr key={cls}>
                      <td>{class_names?.[cls] || cls}</td>
                      <td className="table__mono">{row?.precision != null ? row.precision.toFixed(3) : "—"}</td>
                      <td className="table__mono">{row?.recall != null ? row.recall.toFixed(3) : "—"}</td>
                      <td className="table__mono">{row?.["f1-score"] != null ? row["f1-score"].toFixed(3) : "—"}</td>
                      <td className="table__mono">{row?.support ?? "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card" style={{ margin: 0 }}>
          <h3 className="card__title">Model feature importance</h3>
          <p className="card__sub">
            Global Gini-based importances from the actual model. This explains
            the model as a whole, not an individual prediction.
          </p>
          <BarChart
            items={(metrics?.feature_importances || []).map((fi) => ({
              label: fi.feature,
              value: fi.importance,
            }))}
            valueFormatter={(v) => (v * 100).toFixed(1) + "%"}
          />
        </div>
      </div>
    </>
  );
}