import { useState } from "react";
import { useApi, getErrorMessage } from "../hooks/useApi";
import api from "../api/client";
import State from "../components/Loading";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import Badge from "../components/Badge";
import { useAuth } from "../auth/context";

function formatTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

export default function ModelManagement() {
  const { isAdmin } = useAuth();
  const { data, loading, error, reload } = useApi(() => api.get("/model/versions"));
  const [actionError, setActionError] = useState(null);
  const [busy, setBusy] = useState(null); // "retrain" | version being activated
  const [lastAction, setLastAction] = useState(null);

  const handleRetrain = async () => {
    if (!window.confirm("Retrain a new model version on the current dataset?")) {
      return;
    }
    setActionError(null);
    setLastAction(null);
    setBusy("retrain");
    try {
      const res = await api.post("/model/retrain");
      setLastAction(
        `Version ${res.data.version} registered. ${
          res.data.promoted ? "Activated (metrics within promotion tolerance)." : "Not activated (candidate below tolerance)."
        }`
      );
      reload();
    } catch (err) {
      setActionError(getErrorMessage(err) || "Retraining failed.");
    } finally {
      setBusy(null);
    }
  };

  const handleActivate = async (version) => {
    if (!window.confirm(`Activate model version ${version}? It becomes the serving model immediately.`)) {
      return;
    }
    setActionError(null);
    setLastAction(null);
    setBusy(version);
    try {
      await api.post("/model/activate", { version });
      setLastAction(`Version ${version} is now the active model.`);
      reload();
    } catch (err) {
      setActionError(getErrorMessage(err) || "Activation failed.");
    } finally {
      setBusy(null);
    }
  };

  if (loading) {
    return <State label="Loading model versions..." />;
  }

  if (error) {
    return <ErrorBanner message={`Unable to load model versions. ${error}`} onDismiss={reload} />;
  }

  const history = data?.history || [];

  return (
    <>
      <div className="page-header">
        <h1 className="page-header__title">Model Management</h1>
        <p className="page-header__desc">
          Registered model versions, activation state and retraining controls.
        </p>
      </div>

      {!isAdmin && (
        <ErrorBanner message="Viewer role is read-only. Retraining and activation require an administrator." />
      )}

      {lastAction && (
        <ErrorBanner message={lastAction} onDismiss={() => setLastAction(null)} />
      )}
      {actionError && (
        <ErrorBanner message={actionError} onDismiss={() => setActionError(null)} />
      )}

      {isAdmin && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 className="card__title">Retrain</h3>
          <p className="card__sub" style={{ marginBottom: 12 }}>
            Trains a new Random Forest on <code style={{ fontFamily: "var(--mono)" }}>backend/data/raw/student_data.csv</code>{" "}
            using the same pipeline as initial training. A candidate worse than the active
            model is registered but not activated.
          </p>
          <button type="button" className="btn btn--secondary" onClick={handleRetrain} disabled={busy !== null}>
            {busy === "retrain" ? "Retraining..." : "Retrain new version"}
          </button>
        </div>
      )}

      <div className="card">
        <h3 className="card__title">Versions</h3>
        <p className="card__sub">Serving-model registry</p>

        {history.length === 0 ? (
          <EmptyState compact message="No model versions registered." />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Trained at</th>
                  <th>Accuracy</th>
                  <th>F1 (macro)</th>
                  <th>Status</th>
                  {isAdmin && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {history.map((v) => (
                  <tr key={v.version}>
                    <td className="table__mono">{v.version}</td>
                    <td className="table__muted">{formatTime(v.trained_at)}</td>
                    <td className="table__mono">{v.accuracy != null ? v.accuracy.toFixed(3) : "—"}</td>
                    <td className="table__mono">{v.f1_macro != null ? v.f1_macro.toFixed(3) : "—"}</td>
                    <td>{v.active ? <Badge tone="success">Active</Badge> : <Badge tone="neutral">Inactive</Badge>}</td>
                    {isAdmin && (
                      <td>
                        {!v.active && (
                          <button
                            type="button"
                            className="btn btn--sm btn--secondary"
                            disabled={busy !== null}
                            onClick={() => handleActivate(v.version)}
                          >
                            {busy === v.version ? "Activating..." : "Activate"}
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}