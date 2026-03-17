import { useEffect, useState } from "react";
import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  FileText,
  FolderOpen,
  Globe,
  KeyRound,
  LogOut,
  Pencil,
  ShieldCheck,
  Trash2,
  Upload,
} from "lucide-react";
import {
  getPortfolioSettings,
  updatePortfolioSettings,
  type PortfolioSettings,
} from "../api/portfolioSettings";
import { listResumes, type ResumeListItem } from "../api/outputs";
import { PageContainer, PageHeader } from "../components/shared";

const STAT_CARDS = [
  { label: "Uploads", icon: Upload, accent: "bg-sky-100 text-sky-700" },
  { label: "Projects", icon: FolderOpen, accent: "bg-violet-100 text-violet-700" },
  { label: "Resumes", icon: FileText, accent: "bg-emerald-100 text-emerald-700" },
] as const;

export default function ProfilePage() {
  const username = getUsername();
  const displayName = username;
  const initials = displayName.slice(0, 1).toUpperCase();

  const [settings, setSettings] = useState<PortfolioSettings>({
    portfolio_public: false,
    active_resume_id: null,
  });
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([getPortfolioSettings(), listResumes()])
      .then(([s, resumeRes]) => {
        setSettings(s);
        setResumes(resumeRes.data?.resumes ?? []);
      })
      .catch(() => {})
      .finally(() => setSettingsLoading(false));
  }, []);

  async function togglePublic() {
    setSaving(true);
    try {
      const updated = await updatePortfolioSettings({
        portfolio_public: !settings.portfolio_public,
      });
      setSettings(updated);
    } finally {
      setSaving(false);
    }
  }

  async function handleResumeChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = e.target.value;
    setSaving(true);
    try {
      const updated = await updatePortfolioSettings(
        value === ""
          ? { clear_active_resume: true }
          : { active_resume_id: Number(value) }
      );
      setSettings(updated);
    } finally {
      setSaving(false);
    }
  }

  const publicUrl = `${window.location.origin}/public/${username}/projects`;

  return (
    <>
      <TopBar showNav username={username} />

      <div className="min-h-[calc(100vh-56px)] bg-background">
        <PageContainer className="pt-[12px]">
          <PageHeader
            title="Profile"
            breadcrumbs={[
              { label: "Home", href: "/" },
              { label: "Profile" },
            ]}
          />

          <main className="space-y-0">
            <div className="grid gap-8 lg:grid-cols-[320px_1fr]">
              <aside className="lg:sticky lg:top-24 lg:self-start">
                <Card className="overflow-hidden rounded-2xl border-slate-200/80 bg-white shadow-sm">
                  <div className="relative h-28 bg-gradient-to-r from-indigo-500 via-violet-500 to-sky-500">
                    <Button
                      variant="secondary"
                      size="icon-xs"
                      className="absolute right-3 bottom-3 h-7 w-7 rounded-full border border-white/60 bg-white/85 text-slate-700 hover:bg-white"
                      aria-label="Edit banner"
                    >
                      <Pencil className="size-3.5" />
                    </Button>
                  </div>

                  <CardContent className="relative -mt-10 space-y-4 px-6 pb-6">
                    <div className="relative inline-block">
                      <Avatar className="h-24 w-24 border-4 border-white text-2xl shadow-md">
                        <AvatarFallback className="bg-slate-100 font-semibold text-slate-800">
                          {initials}
                        </AvatarFallback>
                      </Avatar>
                      <Button
                        variant="secondary"
                        size="icon-xs"
                        className="absolute -right-1 -bottom-1 h-7 w-7 rounded-full border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                        aria-label="Edit profile picture"
                      >
                        <Pencil className="size-3.5" />
                      </Button>
                    </div>

                    <div className="space-y-1">
                      <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
                        {displayName}
                      </h1>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-500">@{username}</span>
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          className="h-8 w-8 rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                          aria-label="Edit username"
                        >
                          <Pencil className="size-4" />
                        </Button>
                      </div>
                    </div>

                    <div className="rounded-xl border border-indigo-100 bg-indigo-50 px-3 py-2">
                      <p className="text-xs font-medium text-indigo-700">
                        Profile completeness
                      </p>
                      <p className="mt-1 text-sm text-indigo-900">
                        UI only for now. Backend support implemented later.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </aside>

              <section className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                    Profile overview
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Your account activity, personal information and security
                    controls.
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  {STAT_CARDS.map(({ label, icon: Icon, accent }) => (
                    <Card
                      key={label}
                      className="rounded-2xl border-slate-200/80 bg-white shadow-sm"
                    >
                      <CardContent className="flex items-center gap-4 p-5">
                        <div
                          className={`flex h-11 w-11 items-center justify-center rounded-xl ${accent}`}
                        >
                          <Icon className="size-5" />
                        </div>
                        <div>
                          <p className="text-2xl font-semibold tabular-nums text-slate-900">
                            --
                          </p>
                          <p className="text-sm text-slate-500">{label}</p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm">
                  <CardHeader className="border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <Globe className="size-4 text-slate-500" />
                      <CardTitle className="text-base text-slate-900">
                        Public Portfolio
                      </CardTitle>
                    </div>
                    <CardDescription className="text-slate-500">
                      Control what visitors see at your public portfolio URL.
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-5 pt-6">
                    {settingsLoading ? (
                      <p className="text-sm text-slate-500">Loading…</p>
                    ) : (
                      <>
                        <div className="flex items-center justify-between gap-4">
                          <div>
                            <p className="text-sm font-medium text-slate-800">
                              Portfolio visibility
                            </p>
                            <p className="text-xs text-slate-500">
                              Make your portfolio accessible to anyone with your
                              link.
                            </p>
                          </div>
                          <Button
                            variant={settings.portfolio_public ? "default" : "outline"}
                            size="sm"
                            onClick={togglePublic}
                            disabled={saving}
                            className="shrink-0"
                          >
                            {settings.portfolio_public ? "Public" : "Private"}
                          </Button>
                        </div>

                        {settings.portfolio_public && (
                          <div className="break-all rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-xs text-slate-600 select-all">
                            {publicUrl}
                          </div>
                        )}

                        <div className="space-y-1.5">
                          <p className="text-sm font-medium text-slate-800">
                            Active resume
                          </p>
                          <p className="text-xs text-slate-500">
                            The resume shown on your public portfolio.
                          </p>
                          <select
                            value={settings.active_resume_id ?? ""}
                            onChange={handleResumeChange}
                            disabled={saving}
                            className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 disabled:opacity-60"
                          >
                            <option value="">— None —</option>
                            {resumes.map((r) => (
                              <option key={r.id} value={r.id}>
                                {r.name}
                              </option>
                            ))}
                          </select>
                        </div>

                        <p className="text-xs text-slate-500">
                          To control which projects appear publicly, use the{" "}
                          <a href="/projects" className="text-indigo-600 hover:underline">
                            Projects
                          </a>{" "}
                          page — each card has a Public / Private toggle.
                        </p>
                      </>
                    )}
                  </CardContent>
                </Card>

                <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm">
                  <CardHeader className="border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="size-4 text-slate-500" />
                      <CardTitle className="text-base text-slate-900">
                        Security
                      </CardTitle>
                    </div>
                    <CardDescription className="text-slate-500">
                      Password and account controls (placeholder actions for now).
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-3 pt-6">
                    <Button
                      variant="outline"
                      size="default"
                      className="h-11 w-full justify-start gap-3 border-slate-200 bg-slate-50/60 text-slate-700 hover:bg-slate-100"
                      disabled
                    >
                      <KeyRound className="size-4 text-slate-500" />
                      Change password
                    </Button>

                    <Button
                      variant="outline"
                      size="default"
                      className="h-11 w-full justify-start gap-3 border-slate-200 text-slate-700 hover:bg-slate-50"
                      type="button"
                    >
                      <LogOut className="size-4" />
                      Sign out
                    </Button>

                    <Button
                      variant="ghost"
                      size="default"
                      className="h-11 w-full justify-start gap-3 text-red-600 hover:bg-red-50 hover:text-red-700"
                      type="button"
                    >
                      <Trash2 className="size-4" />
                      Delete account
                    </Button>
                  </CardContent>
                </Card>
              </section>
            </div>
          </main>
        </PageContainer>
      </div>
    </>
  );
}