import { useParams, NavLink, Link } from "react-router-dom";
import type { ReactNode } from "react";
import { tokenStore } from "../../auth/token";
import { getUsername } from "../../auth/user";
import { CircleUserRound } from "../../lib/ui-icons";
import { cn } from "../../lib/utils";

type Props = {
  children: ReactNode;
};

export default function PublicLayout({ children }: Props) {
  const { username } = useParams<{ username: string }>();
  const isLoggedIn = !!tokenStore.get();
  const loggedInUsername = getUsername();

  const navItems = [
    { to: `/public/${username}/projects`, label: "Projects" },
    { to: `/public/${username}/insights`, label: "Insights" },
    { to: `/public/${username}/outputs`, label: "Outputs" },
  ];

  return (
    <>
      <header className="sticky top-0 z-50 h-16 w-full bg-[#001166] text-white">
        <div className="mx-auto flex h-16 w-full max-w-[1140px] items-center justify-between">
          <div className="flex items-baseline gap-3">
            <Link
              to="/"
              className="font-['Open_Sans'] text-4xl font-bold leading-none no-underline text-white"
              aria-label="Go to home"
            >
              resuME
            </Link>
          </div>

          <div className="flex items-center gap-[24px]">
            <nav className="flex items-center gap-[32px]">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "font-['Roboto'] text-base font-normal leading-5 no-underline text-white",
                      isActive && "underline underline-offset-[6px]"
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>

            {isLoggedIn && (
              <Link
                to="/profile"
                className="flex h-7 w-7 items-center justify-center rounded-full bg-[#ECECEC] no-underline"
                aria-label={`Logged in as ${loggedInUsername ?? "user"} — open profile`}
              >
                <CircleUserRound className="h-[18px] w-[18px] text-[#6C6C6C]" strokeWidth={1.8} />
              </Link>
            )}
          </div>
        </div>
      </header>

      {children}
    </>
  );
}
