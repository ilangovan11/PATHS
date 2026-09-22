import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/context";

function Icon({ path }) {
  return (
    <svg
      className="sidebar__icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  );
}

const NAV_ITEMS = [
  {
    to: "/dashboard",
    label: "Dashboard",
    icon: "M3 12l9-8 9 8M5 10v10h5v-6h4v6h5V10",
  },
  {
    to: "/coordinate",
    label: "Coordinate",
    icon: "M12 2a7 7 0 0 1 4 12.7V16h2v6H6v-6h2v-1.3A7 7 0 0 1 12 2z",
  },
  {
    to: "/analytics",
    label: "Analytics",
    icon: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  },
  {
    to: "/model-insights",
    label: "Model Insights",
    icon: "M9.7 3h4.6L21 12l-6.7 9H9.7L3 12l6.7-9zM12 8v4M12 15.5v.5",
  },
];

export default function Layout() {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <span className="sidebar__logo">P</span>
          <div>
            <div className="sidebar__brand-text">PATHS</div>
            <div className="sidebar__brand-sub">Student Risk Decision Support</div>
          </div>
        </div>

        <nav className="sidebar__nav" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? "sidebar__link sidebar__link--active" : "sidebar__link"
              }
            >
              <Icon path={item.icon} />
              {item.label}
            </NavLink>
          ))}

          {isAdmin && (
            <NavLink
              to="/model-management"
              className={({ isActive }) =>
                isActive ? "sidebar__link sidebar__link--active" : "sidebar__link"
              }
            >
              <Icon path="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3" />
              Model Management
            </NavLink>
          )}

          <div className="sidebar__divider" />

          <button
            type="button"
            className="sidebar__link"
            onClick={handleLogout}
            style={{ background: "none", border: "none", cursor: "pointer", width: "100%", textAlign: "left", font: "inherit" }}
          >
            <Icon path="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
            Logout
          </button>
        </nav>

        <div className="sidebar__footer">
          <div className="sidebar__user">{user?.email || "—"}</div>
          <div>
            Role: {user?.role === "admin" ? "Administrator" : "Viewer"}
          </div>
        </div>
      </aside>

      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}