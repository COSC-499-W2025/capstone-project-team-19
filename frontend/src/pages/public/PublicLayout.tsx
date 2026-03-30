import { useParams, NavLink, Link, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, type ReactNode } from "react";
import { tokenStore } from "../../auth/token";
import { getUsername } from "../../auth/user";
import { getPortfolioSettings } from "../../api/portfolioSettings";
import { publicGetPortfolioStatus } from "../../api/public";
import { PageContainer, SectionCard, AppButton } from "../../components/shared";
import { CircleUserRound } from "../../lib/ui-icons";
import { cn } from "../../lib/utils";

type VisitorStatus = "loading" | "public" | "private" | "not_found";

type Props = {
  children: ReactNode;
};

export default function PublicLayout({ children }: Props) {
  const { username } = useParams<{ username: string }>();
  const isLoggedIn = !!tokenStore.get();
  const loggedInUsername = getUsername();
  const location = useLocation();
  const nav = useNavigate();
  const isOwner = isLoggedIn && loggedInUsername === username;
  const [portfolioPublic, setPortfolioPublic] = useState<boolean | null>(null);
  const [visitorStatus, setVisitorStatus] = useState<VisitorStatus>("loading");

  useEffect(() => {
    if (!isOwner) return;
    getPortfolioSettings()
      .then((s) => setPortfolioPublic(s.portfolio_public))
      .catch(() => setPortfolioPublic(false));
  }, [isOwner]);

  useEffect(() => {
    if (isOwner || !username) return;
    publicGetPortfolioStatus(username).then((s) => {
      if (!s.exists) setVisitorStatus("not_found");
      else if (!s.is_public) setVisitorStatus("private");
      else setVisitorStatus("public");
    }).catch(() => setVisitorStatus("not_found"));
  }, [isOwner, username]);

  function getPrivatePath(): string {
    const match = location.pathname.match(/^\/public\/[^/]+\/(.*)$/);
    if (!match) return "/projects";
    const rest = match[1];
    if (rest.startsWith("projects/")) return `/${rest}`;
    if (rest === "projects") return "/projects";
    if (rest === "insights") return "/insights";
    if (rest === "outputs") return "/outputs";
    return "/projects";
  }

  const navItems = [
    { to: `/public/${username}/projects`, label: "Projects" },
    { to: `/public/${username}/insights`, label: "Insights" },
    { to: `/public/${username}/resume`, label: "Resume" },
  ];

  return (
    <>
      <header className="sticky top-0 z-50 h-16 w-full bg-[#001166] text-white">
        <div className="flex h-16 w-full items-center justify-between px-[40px]">
          <Link
            to="/"
            className="font-['Open_Sans'] text-4xl font-bold leading-none no-underline hover:no-underline transition-opacity hover:opacity-80 active:opacity-60"
            aria-label="Go to home"
          >
            resuME
          </Link>

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

            {isLoggedIn && loggedInUsername === username && (
              <div className="flex overflow-hidden rounded-full border border-white/30 text-xs font-medium">
                <button
                  className="cursor-pointer px-3 py-1.5 text-white/75 transition-colors hover:bg-white/10 hover:text-white"
                  onClick={() => nav(getPrivatePath())}
                >
                  Private
                </button>
                <span className="cursor-default bg-white px-3 py-1.5 text-[#001166]">
                  Public
                </span>
              </div>
            )}

            {isLoggedIn && (
              <Link
                to="/profile"
                className="flex h-7 w-7 items-center justify-center rounded-full bg-[#ECECEC] no-underline hover:no-underline"
                aria-label={`Logged in as ${loggedInUsername ?? "user"} — open profile`}
              >
                <CircleUserRound className="h-[18px] w-[18px] text-[#6C6C6C]" strokeWidth={1.8} />
              </Link>
            )}

            {loggedInUsername !== username && visitorStatus === "public" && (
              <span className="font-['Roboto'] text-sm text-white/60">
                Viewing {username}&apos;s portfolio
              </span>
            )}
          </div>
        </div>
      </header>

      {isOwner && portfolioPublic === false ? (
        <PageContainer>
          <SectionCard className="flex flex-col items-center gap-4 py-10 text-center">
            <p className="text-[14px] text-[#7f7f7f]">
              Your portfolio is set to private. Enable public viewing in your profile to share this page.
            </p>
            <AppButton variant="primary" onClick={() => nav("/profile")}>
              Go to Profile
            </AppButton>
          </SectionCard>
        </PageContainer>
      ) : !isOwner && visitorStatus === "not_found" ? (
        <PageContainer>
          <SectionCard className="flex flex-col items-center gap-4 py-10 text-center">
            <p className="text-[14px] text-[#7f7f7f]">
              This user does not exist.
            </p>
          </SectionCard>
        </PageContainer>
      ) : !isOwner && visitorStatus === "private" ? (
        <PageContainer>
          <SectionCard className="flex flex-col items-center gap-4 py-10 text-center">
            <p className="text-[14px] text-[#7f7f7f]">
              <strong>{username}</strong>&apos;s portfolio is not public. Ask them to enable public access in their profile settings.
            </p>
          </SectionCard>
        </PageContainer>
      ) : !isOwner && visitorStatus === "loading" ? null : children}
    </>
  );
}
