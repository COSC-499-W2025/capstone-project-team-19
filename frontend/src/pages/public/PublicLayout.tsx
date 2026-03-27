import { useParams, NavLink, Link } from "react-router-dom";
import type { ReactNode } from "react";
import { tokenStore } from "../../auth/token";
import { getUsername } from "../../auth/user";

type Props = {
  children: ReactNode;
};

export default function PublicLayout({ children }: Props) {
  const { username } = useParams<{ username: string }>();
  const isLoggedIn = !!tokenStore.get();
  const loggedInUsername = getUsername();

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
            <span className="username" style={{ opacity: 0.6 }}>
              Viewing {username}&apos;s portfolio
            </span>
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
