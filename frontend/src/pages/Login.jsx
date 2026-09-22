import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../auth/context";
import { getErrorMessage } from "../hooks/useApi";
import ErrorBanner from "../components/ErrorBanner";

export default function Login() {
  const { token, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  if (token) {
    return <Navigate to="/dashboard" replace />;
  }

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err) || "Login failed. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <div className="login-card__brand">
          <span className="sidebar__logo">P</span>
          <div>
            <div className="login-card__title">PATHS</div>
            <div className="login-card__sub">Student Risk Decision Support</div>
          </div>
        </div>

        <h2>Sign in</h2>
        <p style={{ color: "var(--text-muted)", margin: "6px 0 18px", fontSize: 13 }}>
          Authenticate to continue to the dashboard.
        </p>

        {error && <ErrorBanner message={error} />}

        <div className="field" style={{ marginBottom: 14 }}>
          <label htmlFor="email" className="field__label">
            Email
          </label>
          <input
            id="email"
            type="email"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="username"
            required
          />
        </div>

        <div className="field" style={{ marginBottom: 18 }}>
          <label htmlFor="password" className="field__label">
            Password
          </label>
          <input
            id="password"
            type="password"
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        <button type="submit" className="btn btn--primary" disabled={busy} style={{ width: "100%" }}>
          {busy ? "Signing in..." : "Sign in"}
        </button>

        <div className="login-card__note">
          Demonstration credentials:
          <div className="demo-hint">
            Admin: <code>admin@paths.io</code> / <code>admin123</code>
            <br />
            Viewer: <code>viewer@paths.io</code> / <code>viewer123</code>
          </div>
        </div>
      </form>
    </div>
  );
}