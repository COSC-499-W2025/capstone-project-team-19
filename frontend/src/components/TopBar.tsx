import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { CircleUserRound } from "../lib/ui-icons";
import { cn } from "../lib/utils";

type Props = {
  showNav?: boolean;
  username?: string;
};

const navItems = [
  { to: "/upload", label: "Upload" },
  { to: "/projects", label: "Projects" },
  { to: "/insights", label: "Insights" },
  { to: "/outputs", label: "Outputs" },
];

const privateToPublicSection: Record<string, string> = {
  projects: "projects",
  insights: "insights",
  outputs: "outputs",
};

function getPublicPath(pathname: string, username: string): string {
  const segment = pathname.split("/").filter(Boolean)[0] ?? "projects";
  const section = privateToPublicSection[segment] ?? "projects";
  return `/public/${username}/${section}`;
}

export default function TopBar({ showNav = false, username }: Props) {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-50 h-16 w-full bg-[#001166] text-white">
      <div className="mx-auto flex h-16 w-full max-w-[1140px] items-center justify-between">
        <Link
          to="/"
          className="font-['Open_Sans'] text-4xl font-bold leading-none no-underline"
          aria-label="Go to home"
        >
          resuME
        </Link>

        {showNav && (
          <div className="flex items-center gap-[24px]">
            <nav className="flex items-center gap-[32px]">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "font-['Roboto'] text-base font-normal leading-5 no-underline",
                      isActive && "underline underline-offset-[6px]"
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>

            {username && (
              <div className="flex items-center rounded-full border border-white/40 text-sm">
                <button
                  className="rounded-l-full bg-white px-3 py-1 font-medium text-[#001166]"
                  disabled
                >
                  Private
                </button>
                <button
                  className="rounded-r-full px-3 py-1 font-medium text-white/80 hover:text-white"
                  onClick={() => navigate(getPublicPath(location.pathname, username))}
                >
                  Public
                </button>
              </div>
            )}

            <Link
              to="/profile"
              className="flex h-7 w-7 items-center justify-center rounded-full bg-[#ECECEC] no-underline"
              aria-label="Open profile"
            >
              <CircleUserRound
                className="h-[18px] w-[18px] text-[#6C6C6C]"
                strokeWidth={1.8}
              />
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}