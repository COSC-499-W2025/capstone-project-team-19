import { useParams, NavLink, Link, useLocation, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { tokenStore } from "../../auth/token";
import { getUsername } from "../../auth/user";

type Props = {
  children: ReactNode;
};

const publicToPrivateSection: Record<string, string> = {
  projects: "/projects",
  insights: "/insights",
  outputs: "/outputs",
};

function getPrivatePath(pathname: string): string {
  // pathname: /public/:username/section
  const parts = pathname.split("/").filter(Boolean);
  const section = parts[2] ?? "projects";
  return publicToPrivateSection[section] ?? "/projects";
}

export default function PublicLayout({ children }: Props) {
  const { username } = useParams<{ username: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const isLoggedIn = !!tokenStore.get();
  const loggedInUsername = getUsername();
  const isOwner = isLoggedIn && loggedInUsername === username;

  return (
    <>
      <div className="topbar">
        <div className="topbarInner" style={{ position: "relative" }}>
          <Link to="/" className="brandLink" aria-label="Go to home">
            <div className="brand">resuME</div>
          </Link>

          <nav className="nav" style={{ position: "absolute", left: "50%", transform: "translateX(-50%)" }}>
            <NavLink className="navLink" to={`/public/${username}/projects`}>
              Projects
            </NavLink>
            <span className="navSep">|</span>
            <NavLink className="navLink" to={`/public/${username}/insights`}>
              Insights
            </NavLink>
            <span className="navSep">|</span>
            <NavLink className="navLink" to={`/public/${username}/outputs`}>
              Outputs
            </NavLink>
          </nav>

          <div className="userArea">
            {isOwner ? (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  borderRadius: "9999px",
                  border: "1px solid rgba(255,255,255,0.4)",
                  fontSize: "0.875rem",
                  overflow: "hidden",
                }}
              >
                <button
                  style={{
                    padding: "4px 12px",
                    background: "transparent",
                    color: "rgba(255,255,255,0.8)",
                    fontWeight: 500,
                    border: "none",
                    cursor: "pointer",
                  }}
                  onClick={() => navigate(getPrivatePath(location.pathname))}
                >
                  Private
                </button>
                <button
                  style={{
                    padding: "4px 12px",
                    background: "white",
                    color: "#001166",
                    fontWeight: 500,
                    border: "none",
                    cursor: "default",
                  }}
                  disabled
                >
                  Public
                </button>
              </div>
            ) : (
              <span className="username" style={{ opacity: 0.6 }}>
                Viewing {username}&apos;s portfolio
              </span>
            )}
            {isLoggedIn && (
              <>
                <Link to="/profile" className="navLink" aria-label="Open profile">
                  <div className="avatar" />
                </Link>
                <Link to="/profile" className="username" aria-label="Open profile">
                  {loggedInUsername ?? "username"}
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {children}
    </>
  );
}
