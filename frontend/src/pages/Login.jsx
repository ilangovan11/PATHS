import { useContext, useState } from "react";
import { AuthContext } from "../auth/AuthContext";

export default function Login() {
  const { login } = useContext(AuthContext);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = async () => {
    try {
      await login(email, password);
    } catch {
      setError(err.response?.data?.detail || "Login failed");
    }
  };

  return (
    <div className="center">
      <h2>ACCESS THE COORDINATE</h2>
      <input placeholder="Email" onChange={e => setEmail(e.target.value)} />
      <input type="password" placeholder="Password" onChange={e => setPassword(e.target.value)} />
      <button onClick={submit}>ENTER</button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}