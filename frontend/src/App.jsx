import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Coordinate from "./pages/Coordinate";
import Analytics from "./pages/Analytics";
import ModelInsights from "./pages/ModelInsights";
import ModelManagement from "./pages/ModelManagement";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/coordinate" element={<Coordinate />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/model-insights" element={<ModelInsights />} />
          <Route path="/model-management" element={<ModelManagement />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}