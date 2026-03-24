import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { CircleUserRound } from "../lib/ui-icons";
import { cn } from "../lib/utils";
import { getUsername } from "../auth/user";

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

export default function TopBar({ showNav = false }: Props) {
  const location = useLocation();
  const nav = useNavigate();
  const username = getUsername();

  function getPublicPath(): string {
    const p = location.pathname;
    if (!username) return "/";
    if (p.startsWith("/projects/")) return `/public/${username}${p}`;
    if (p.startsWith("/projects")) return `/public/${username}/projects`;
    if (p.startsWith("/insights")) return `/public/${username}/insights`;
    if (p.startsWith("/outputs")) return `/public/${username}/outputs`;
    return `/public/${username}/projects`;
  }

  return (
    <header className="sticky top-0 z-50 h-16 w-full bg-[#001166] text-white">
      <div className="flex h-16 w-full items-center justify-between px-[40px]">
        <Link
          to="/"
          className="font-['Open_Sans'] text-4xl font-bold leading-none no-underline hover:no-underline transition-opacity hover:opacity-80 active:opacity-60"
          aria-label="Go to home"
        >
          resuME
        </Link>

        {showNav && (
          <div className="flex items-center gap-[24px]">
            <nav className="flex h-16 items-center gap-[32px]">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "group relative flex h-full items-center font-['Roboto'] text-base font-normal leading-5 no-underline hover:no-underline",
                      isActive ? "text-white" : "text-white/75 hover:text-white"
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      {item.label}
                      <span
                        className={cn(
                          "absolute bottom-0 left-0 right-0 h-[3px] rounded-t-[2px] transition-opacity",
                          isActive
                            ? "bg-white opacity-100"
                            : "bg-white opacity-0 group-hover:opacity-100"
                        )}
                      />
                    </>
                  )}
                </NavLink>
              ))}
            </nav>

            <div className="flex overflow-hidden rounded-full border border-white/30 text-xs font-medium">
              <span className="cursor-default bg-white px-3 py-1.5 text-[#001166]">
                Private
              </span>
              <button
                className="cursor-pointer px-3 py-1.5 text-white/75 transition-colors hover:bg-white/10 hover:text-white"
                onClick={() => nav(getPublicPath())}
              >
                Public
              </button>
            </div>

            <Link
              to="/profile"
              className="flex h-7 w-7 items-center justify-center rounded-full bg-[#ECECEC] no-underline hover:no-underline"
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