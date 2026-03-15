import { Link, NavLink } from "react-router-dom";
import { cn } from "../lib/utils";
import { CircleUserRound } from "../lib/ui-icons.ts";

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

export default function TopBar({ showNav = false, username }: Props) {
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-primary text-primary-foreground">
      <div className="mx-auto flex h-16 w-full max-w-[1200px] items-center justify-between px-6">
        <Link
          to="/"
          className="logoText text-[30px] leading-none text-primary-foreground no-underline"
          aria-label="Go to home"
        >
          resuME
        </Link>

        {showNav && (
          <div className="flex items-center gap-6">
            <nav className="flex items-center gap-5 text-sm">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "text-primary-foreground/80 no-underline transition hover:text-primary-foreground",
                      isActive && "text-primary-foreground underline underline-offset-4"
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>

            <Link
              to="/profile"
              className="flex items-center gap-2 text-primary-foreground no-underline"
              aria-label="Open profile"
            >
              <CircleUserRound className="h-5 w-5" />
              <span className="text-sm font-medium">{username ?? "username"}</span>
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}