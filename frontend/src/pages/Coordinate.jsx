import { useState } from "react";
import api from "../api/client";
import { getErrorMessage } from "../hooks/useApi";
import ErrorBanner from "../components/ErrorBanner";
import Badge from "../components/Badge";
import BarChart from "../components/BarChart";
import { useAuth } from "../auth/context";
import { ACTION_TONES } from "../constants";

const FEATURES = {
  attendance: { label: "Attendance", min: 0, max: 100, unit: "%", hint: "0–100%" },
  internal_marks: { label: "Internal Marks", min: 0, max: 100, unit: "", hint: "0–100" },
  assignments: { label: "Assignments", min: 0, max: 100, unit: "%", hint: "0–100%" },
  study_hours: { label: "Daily Study Hours", min: 0, max: 16, step: 0.5, unit: "h", hint: "0–16 hours/day" },
  backlog_count: { label: "Backlog Subjects", min: 0, max: 20, unit: "", hint: "0–20 subjects" },
  stress_level: { label: "Stress Level", min: 1, max: 10, unit: "/10", hint: "1–10" },
};

const PROB_COLORS = {
  ADVANCE: "#15803d",
  HOLD: "#b45309",
  RETREAT: "#b91c1c",
};

const INITIAL = {
  attendance: "",
  internal_marks: "",
  assignments: "",
  study_hours: "",
  backlog_count: "",
  stress_level: "",
};

function formatPct(v) {
  return v != null ? `${(v * 100).toFixed(1)}%` : "—";
}

export default function Coordinate() {
  const { isAdmin } = useAuth();
  const [form, setForm] = useState(INITIAL);
  const [fieldErrors, setFieldErrors] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  const setField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
    setFieldErrors((e) => ({ ...e, [key]: null }));
  };

  const validate = () => {
    const errors = {};
    for (const [key, spec] of Object.entries(FEATURES)) {
      const raw = form[key];
      if (raw === "" || raw === null) {
        errors[key] = "Required";
        continue;
      }
      const value = Number(raw);
      if (Number.isNaN(value)) {
        errors[key] = "Must be a number";
      } else if (value < spec.min || value > spec.max) {
        errors[key] = `Range ${spec.min}–${spec.max}`;
      }
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const analyze = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    if (!validate()) {
      return;
    }
    if (!isAdmin) {
      setError("Only administrators can run new decisions.");
      return;
    }
    setAnalyzing(true);
    try {
      const payload = Object.fromEntries(
        Object.keys(FEATURES).map((k) => [k, Number(form[k])])
      );
      const res = await api.post("/coordinate", payload);
      setResult(res.data);
    } catch (err) {
      setError(getErrorMessage(err) || "Analysis failed. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  const inputGroup = (keys, title) => (
    <fieldset className="form-section" style={{ margin: 0 }}>
      <legend className="form-section__title">{title}</legend>
      <div className="form-grid">
        {keys.map((key) => {
          const spec = FEATURES[key];
          return (
            <div className="field" key={key}>
              <label className="field__label" htmlFor={`field-${key}`}>
                {spec.label}
                <span className="field__hint" style={{ fontWeight: 400 }}>
                  {" "}
                  · {spec.hint}
                </span>
              </label>
              <input
                id={`field-${key}`}
                className="input"
                type="number"
                inputMode="numeric"
                min={spec.min}
                max={spec.max}
                step={spec.step || 1}
                value={form[key]}
                onChange={(ev) => setField(key, ev.target.value)}
              />
              {fieldErrors[key] && (
                <span className="field__error" role="alert">
                  {fieldErrors[key]}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </fieldset>
  );

  return (
    <>
      <div className="page-header">
        <h1 className="page-header__title">Coordinate</h1>
        <p className="page-header__desc">
          Enter a student's indicators to run the risk decision pipeline.
        </p>
      </div>

      {!isAdmin && (
        <ErrorBanner message="Viewer role is read-only. Running a new decision requires an administrator account." />
      )}

      <div className="card-row grid-2">
        <form className="card" style={{ margin: 0 }} onSubmit={analyze} noValidate>
          <h3 className="card__title">Student indicators</h3>
          <p className="card__sub">
            Academic and study indicators used by the model.
          </p>

          {inputGroup(["attendance", "internal_marks", "assignments"], "Academic performance")}
          {inputGroup(["study_hours", "backlog_count", "stress_level"], "Study & risk")}

          <button
            type="submit"
            className="btn btn--primary"
            disabled={analyzing || !isAdmin}
            style={{ width: "100%" }}
          >
            {analyzing ? "Analyzing..." : "Analyze Student"}
          </button>

          {error && (
            <div style={{ marginTop: 14 }}>
              <ErrorBanner message={error} />
            </div>
          )}
        </form>

        <section className="card" style={{ margin: 0 }} aria-live="polite">
          <h3 className="card__title">Analysis result</h3>
          <p className="card__sub">The decision produced by the safety-rules layer.</p>

          {!result && !analyzing && (
            <div className="state">
              <span aria-hidden="true" style={{ fontSize: 30 }}>⟶</span>
              <span>Submit the form to generate a decision.</span>
            </div>
          )}

          {analyzing && !result && (
            <div className="state">
              <div className="spinner" role="status" aria-label="Analyzing" />
              <span>Running ML prediction and safety rules...</span>
            </div>
          )}

          {result && (
            <div>
              <div className={`decision-hero decision-hero--${result.action}`}>
                <div>
                  <div className="decision-hero__label">Final Decision</div>
                  <div className="decision-hero__value">{result.action}</div>
                </div>
                <div className="decision-hero__side">
                  <div className="decision-hero__conf">
                    {formatPct(result.confidence)}
                  </div>
                  <div className="decision-hero__meta">model confidence</div>
                  <div className="decision-hero__meta">
                    model {result.model_version} · predicted {result.prediction}
                  </div>
                </div>
              </div>

              <div className="card" style={{ borderColor: "var(--border)", boxShadow: "none" }}>
                <h3 className="card__title">Reason</h3>
                <p style={{ color: "var(--text-muted)", marginBottom: 12 }}>{result.reason}</p>
              </div>

              <div className="card" style={{ borderColor: "var(--border)", boxShadow: "none" }}>
                <h3 className="card__title">Class probabilities</h3>
                <BarChart
                  items={Object.entries(result.probabilities || {}).map(([cls, value]) => ({
                    label: result.class_names?.[cls] || cls,
                    value,
                    color: PROB_COLORS[result.class_names?.[cls]] || "var(--primary)",
                  }))}
                  valueFormatter={formatPct}
                />
              </div>

              <div className="card" style={{ borderColor: "var(--border)", boxShadow: "none" }}>
                <h3 className="card__title">Decision trace</h3>
                <ol className="trace">
                  {result.trace.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </div>

              <div className="card" style={{ borderColor: "var(--border)", boxShadow: "none" }}>
                <h3 className="card__title">Rules checked</h3>
                <div className="rule-list">
                  {result.rules_checked.map((rule) => (
                    <div className="rule-row" key={rule.rule}>
                      <Badge tone={rule.triggered ? "info" : "neutral"}>
                        {rule.triggered ? "fired" : "passed"}
                      </Badge>
                      <div className="rule-row__body">
                        <div className="rule-row__name">{rule.rule}</div>
                        <div className="rule-row__condition">{rule.condition}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card" style={{ borderColor: "var(--border)", boxShadow: "none" }}>
                <h3 className="card__title">Model feature importance</h3>
                <p className="card__sub">
                  Global model-level importance from the active Random Forest,
                  not an individual attribution.
                </p>
                <BarChart
                  items={(result.feature_importances || []).map((fi) => ({
                    label: fi.feature,
                    value: fi.importance,
                  }))}
                  valueFormatter={(v) => (v * 100).toFixed(1) + "%"}
                />
              </div>
            </div>
          )}
        </section>
      </div>
    </>
  );
}