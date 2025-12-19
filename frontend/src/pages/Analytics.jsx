import { useEffect, useState } from "react";
import api from "../api/client";

export default function Analytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/analytics/summary").then(res => setData(res.data));
  }, []);

  if (!data) return null;

  return (
    <div className="page">
      <h2>INTELLIGENCE REPORT</h2>
      <p>Total: {data.total_decisions}</p>
      <p>Advance: {data.advance}</p>
      <p>Hold: {data.hold}</p>
      <p>Retreat: {data.retreat}</p>
    </div>
  );
}