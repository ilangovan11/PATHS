import { useState } from "react";
import api from "../api/client";

export default function Coordinate() {
  const [form, setForm] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/coordinate", form);
      setResult(res.data);
    } catch (err) {
      setError("Execution failed. Check inputs or auth.");
    }
    setLoading(false);
  };

  return (
    <div className="page">
      <h2>THE COORDINATE</h2>

      {[
        "attendance",
        "internal_marks",
        "assignments",
        "study_hours",
        "backlog_count",
        "stress_level"
      ].map(k => (
        <input
          key={k}
          placeholder={k}
          type="number"
          onChange={e =>
            setForm({ ...form, [k]: Number(e.target.value) })
          }
        />
      ))}

      <button onClick={submit} disabled={loading}>
        {loading ? "EXECUTING..." : "EXECUTE"}
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {result && (
        <div className="card">
          <h3>{result.action}</h3>
          <p>Confidence: {result.confidence}</p>
          <p>{result.reason}</p>
        </div>
      )}
    </div>
  );
}