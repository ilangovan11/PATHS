import { useContext, useState, useEffect } from "react";
import { AuthProvider, AuthContext } from "./auth/AuthContext";
import Login from "./pages/Login";
import Coordinate from "./pages/Coordinate";
import Analytics from "./pages/Analytics";

function AppContent() {
  const { token, logout } = useContext(AuthContext);
  const [page, setPage] = useState("coordinate");

  useEffect(() => {
    if (!token) {
      setPage("coordinate");
    }
  }, [token]);

  if (!token) {
    return <Login />;
  }

  return (
    <div>
      <nav style={{ display: "flex", gap: "10px", padding: "10px" }}>
        <button onClick={() => setPage("coordinate")}>Coordinate</button>
        <button onClick={() => setPage("analytics")}>Analytics</button>
        <button
          onClick={() => {
            logout();
            setPage("coordinate");
          }}
        >
          Logout
        </button>
      </nav>

      {page === "coordinate" && <Coordinate />}
      {page === "analytics" && <Analytics />}
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}