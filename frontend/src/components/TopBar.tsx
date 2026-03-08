import { Link, NavLink } from "react-router-dom";

type Props = {
  showNav?: boolean;
  username?: string;
};

export default function TopBar({ showNav = false, username }: Props) {
  return (
    <div className="topbar">
      <div className="topbarInner">
        <Link to="/" className="brandLink" aria-label="Go to home">
          <div className="brand">resuME</div>
        </Link>

        {showNav && (
          <nav className="nav">
            <NavLink className="navLink" to="/upload/consent">
              Upload
            </NavLink>
            <span className="navSep">|</span>
            <NavLink className="navLink" to="/projects">
              Projects
            </NavLink>
            <span className="navSep">|</span>
            <NavLink className="navLink" to="/insights">
              Insights
            </NavLink>
            <span className="navSep">|</span>
            <NavLink className="navLink" to="/outputs">
              Outputs
            </NavLink>
          </nav>
        )}

        {showNav && (
          <div className="userArea">
            <div className="avatar" />
            <div className="username">{username ?? "username"}</div>
          </div>
        )}
      </div>
    </div>
  );
}
