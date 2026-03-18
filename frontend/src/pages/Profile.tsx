import { useEffect, useState } from "react";
import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Globe, KeyRound, LogOut, Pencil, ShieldCheck, Trash2 } from "lucide-react";
import {
  getProfile,
  updateProfile,
  getEducation,
  replaceEducation,
  getCertifications,
  replaceCertifications,
  type UserProfile,
  type UserEducationEntry,
  getExperience,
  replaceExperience,
  type UserExperienceEntry,
} from "../api/profile";
import {
  getPortfolioSettings,
  updatePortfolioSettings,
  type PortfolioSettings,
} from "../api/portfolioSettings";
import { listResumes, type ResumeListItem } from "../api/outputs";

type EditableEducationEntry = Omit<UserEducationEntry, "entry_id" | "entry_type" | "display_order" | "created_at" | "updated_at">;
type EditableExperienceEntry = Omit<UserExperienceEntry, "entry_id" | "display_order" | "created_at" | "updated_at">;

export default function ProfilePage() {
  const username = getUsername();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [education, setEducation] = useState<UserEducationEntry[]>([]);
  const [certifications, setCertifications] = useState<UserEducationEntry[]>([]);
  const [experience, setExperience] = useState<UserExperienceEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const [editingProfile, setEditingProfile] = useState(false);
  const [editingEducation, setEditingEducation] = useState(false);
  const [editingCerts, setEditingCerts] = useState(false);
  const [editingExperience, setEditingExperience] = useState(false);

  const [editingSummary, setEditingSummary] = useState(false);
  const [summaryDraft, setSummaryDraft] = useState("");

  const [profileDraft, setProfileDraft] = useState<Partial<UserProfile>>({});
  const [educationDraft, setEducationDraft] = useState<EditableEducationEntry[]>([]);
  const [certsDraft, setCertsDraft] = useState<EditableEducationEntry[]>([]);
  const [experienceDraft, setExperienceDraft] = useState<EditableExperienceEntry[]>([]);

  const [settings, setSettings] = useState<PortfolioSettings>({
    portfolio_public: false,
    active_resume_id: null,
  });
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getProfile(),
      getEducation(),
      getCertifications(),
      getExperience(),
      getPortfolioSettings(),
      listResumes(),
    ])
      .then(([p, edu, certs, exp, s, resumeRes]) => {
        setProfile(p);
        setEducation(edu.entries);
        setCertifications(certs.entries);
        setExperience(exp.entries);
        setSettings(s);
        setResumes(resumeRes.data?.resumes ?? []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
    setSettingsLoading(false);
  }, []);

  function startEditProfile() {
    if (!profile) return;
    setProfileDraft(profile);
    setEditingProfile(true);
  }

  async function saveProfile() {
    if (!profile) return;
    try {
      const updated = await updateProfile({
        email: profileDraft.email ?? profile.email ?? "",
        full_name: profileDraft.full_name ?? profile.full_name ?? "",
        phone: profileDraft.phone ?? profile.phone ?? "",
        linkedin: profileDraft.linkedin ?? profile.linkedin ?? "",
        github: profileDraft.github ?? profile.github ?? "",
        location: profileDraft.location ?? profile.location ?? "",
      });
      setProfile(updated);
      setEditingProfile(false);
    } catch (e) {
      // error is surfaced via toast in real UI; for now silently ignore
    }
  }

  function startEditEducation() {
    setEducationDraft(
      education.map((e) => ({
        title: e.title,
        organization: e.organization,
        date_text: e.date_text,
        description: e.description,
      })),
    );
    if (education.length === 0) {
      setEducationDraft([
        { title: "", organization: "", date_text: "", description: "" },
      ]);
    }
    setEditingEducation(true);
  }

  async function saveEducation() {
    try {
      const cleaned = educationDraft.filter((e) => e.title.trim() !== "");
      const updated = await replaceEducation({ entries: cleaned });
      setEducation(updated.entries);
      setEditingEducation(false);
    } catch {
      // ignore for now
    }
  }

  function startEditCerts() {
    setCertsDraft(
      certifications.map((e) => ({
        title: e.title,
        organization: e.organization,
        date_text: e.date_text,
        description: e.description,
      })),
    );
    if (certifications.length === 0) {
      setCertsDraft([
        { title: "", organization: "", date_text: "", description: "" },
      ]);
    }
    setEditingCerts(true);
  }

  async function saveCerts() {
    try {
      const cleaned = certsDraft.filter((e) => e.title.trim() !== "");
      const updated = await replaceCertifications({ entries: cleaned });
      setCertifications(updated.entries);
      setEditingCerts(false);
    } catch {
      // ignore for now
    }
  }

  function startEditExperience() {
    setExperienceDraft(
      experience.map((e) => ({
        role: e.role,
        company: e.company,
        date_text: e.date_text,
        description: e.description,
      })),
    );
    if (experience.length === 0) {
      setExperienceDraft([
        { role: "", company: "", date_text: "", description: "" },
      ]);
    }
    setEditingExperience(true);
  }

  async function saveExperience() {
    try {
      const cleaned = experienceDraft.filter((e) => e.role.trim() !== "");
      const updated = await replaceExperience({ entries: cleaned });
      setExperience(updated.entries);
      setEditingExperience(false);
    } catch {
      // ignore for now
    }
  }

  function startEditSummary() {
    if (!profile) return;
    setSummaryDraft(profile.profile_text ?? "");
    setEditingSummary(true);
  }

  async function saveSummary() {
    if (!profile) return;
    try {
      const updated = await updateProfile({
        profile_text: summaryDraft,
      });
      setProfile(updated);
      setEditingSummary(false);
    } catch {
      // ignore for now
    }
  }

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
          : { active_resume_id: Number(value) },
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
      <main className="min-h-[calc(100vh-56px)] bg-gradient-to-b from-slate-50 via-white to-slate-100/40">
        <div className="mx-auto w-full max-w-6xl px-6 py-10">
          <div className="grid gap-8 lg:grid-cols-[320px_1fr]">
            <aside className="lg:self-start">
              <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm">
                <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-slate-100">
                  <div>
                    <p className="text-base font-medium text-slate-800">@{username}</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-1 gap-2"
                    onClick={editingProfile ? saveProfile : startEditProfile}
                    disabled={loading || (!profile && !editingProfile)}
                  >
                    <Pencil className="size-4" />
                    {editingProfile ? "Save" : "Edit"}
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4 pt-5">
                  {loading || !profile ? (
                    <p className="text-sm text-slate-500">Loading profile…</p>
                  ) : editingProfile ? (
                    <div className="space-y-3">
                      <div>
                        <label className="mb-1 block text-xs font-medium text-slate-600">
                          Full name
                        </label>
                        <Input
                          value={profileDraft.full_name ?? profile.full_name ?? ""}
                          onChange={(e) =>
                            setProfileDraft((d) => ({ ...d, full_name: e.target.value }))
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-medium text-slate-600">
                          Email
                        </label>
                        <Input
                          value={profileDraft.email ?? profile.email ?? ""}
                          onChange={(e) =>
                            setProfileDraft((d) => ({ ...d, email: e.target.value }))
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-medium text-slate-600">
                          Phone
                        </label>
                        <Input
                          value={profileDraft.phone ?? profile.phone ?? ""}
                          onChange={(e) =>
                            setProfileDraft((d) => ({ ...d, phone: e.target.value }))
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-medium text-slate-600">
                          Location
                        </label>
                        <Input
                          value={profileDraft.location ?? profile.location ?? ""}
                          onChange={(e) =>
                            setProfileDraft((d) => ({ ...d, location: e.target.value }))
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-medium text-slate-600">
                          LinkedIn URL
                        </label>
                        <Input
                          value={profileDraft.linkedin ?? profile.linkedin ?? ""}
                          onChange={(e) =>
                            setProfileDraft((d) => ({ ...d, linkedin: e.target.value }))
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-medium text-slate-600">
                          GitHub URL
                        </label>
                        <Input
                          value={profileDraft.github ?? profile.github ?? ""}
                          onChange={(e) =>
                            setProfileDraft((d) => ({ ...d, github: e.target.value }))
                          }
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <ProfileField label="Full name" value={profile.full_name} />
                      <ProfileField label="Email" value={profile.email} />
                      <ProfileField label="Phone" value={profile.phone} />
                      <ProfileField label="Location" value={profile.location} />
                      <ProfileField label="LinkedIn" value={profile.linkedin} isLink />
                      <ProfileField label="GitHub" value={profile.github} isLink />
                    </div>
                  )}
                </CardContent>
              </Card>
            </aside>

            <section className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold tracking-tight text-slate-900">Profile overview</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Manage the information that appears on your resumes and portfolio, plus your account
                  security.
                </p>
              </div>

              {/* Profile summary */}
              <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm">
                <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-slate-100">
                  <div>
                    <CardTitle className="text-base text-slate-900">Profile summary</CardTitle>
                    <CardDescription className="text-slate-500">
                      A short paragraph that appears at the top of your resumes.
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-1 gap-2"
                    onClick={editingSummary ? saveSummary : startEditSummary}
                    disabled={loading || (!profile && !editingSummary)}
                  >
                    <Pencil className="size-4" />
                    {editingSummary ? "Save" : "Edit"}
                  </Button>
                </CardHeader>
                <CardContent className="space-y-3 pt-6">
                  {loading || !profile ? (
                    <p className="text-sm text-slate-500">Loading profile…</p>
                  ) : editingSummary ? (
                    <div>
                      <Textarea
                        rows={4}
                        value={summaryDraft}
                        onChange={(e) => setSummaryDraft(e.target.value)}
                      />
                    </div>
                  ) : (
                    <p className="text-sm text-slate-700 whitespace-pre-line">
                      {profile.profile_text || "Not added yet."}
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Education */}
              <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm">
                <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-slate-100">
                  <div>
                    <CardTitle className="text-base text-slate-900">Education</CardTitle>
                    <CardDescription className="text-slate-500">
                      Degrees and academic programs to include on your resumes.
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-1 gap-2"
                    onClick={editingEducation ? saveEducation : startEditEducation}
                    disabled={loading}
                  >
                    <Pencil className="size-4" />
                    {editingEducation ? "Save" : "Edit"}
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4 pt-6">
                  {loading ? (
                    <p className="text-sm text-slate-500">Loading education…</p>
                  ) : editingEducation ? (
                    <EditableEntriesList entries={educationDraft} setEntries={setEducationDraft} />
                  ) : education.length === 0 ? (
                    <p className="text-sm text-slate-500">
                      No education added yet. Add entries to show your degrees and programs on exported
                      resumes.
                    </p>
                  ) : (
                    <EntriesDisplay entries={education} emptyMessage="" />
                  )}
                </CardContent>
              </Card>

              {/* Experience */}
              <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm">
                <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-slate-100">
                  <div>
                    <CardTitle className="text-base text-slate-900">Experience</CardTitle>
                    <CardDescription className="text-slate-500">
                      Work experience and internships to include on your resumes.
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-1 gap-2"
                    onClick={editingExperience ? saveExperience : startEditExperience}
                    disabled={loading}
                  >
                    <Pencil className="size-4" />
                    {editingExperience ? "Save" : "Edit"}
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4 pt-6">
                  {loading ? (
                    <p className="text-sm text-slate-500">Loading experience…</p>
                  ) : editingExperience ? (
                    <EditableExperienceList
                      entries={experienceDraft}
                      setEntries={setExperienceDraft}
                    />
                  ) : experience.length === 0 ? (
                    <p className="text-sm text-slate-500">
                      No experience added yet. Add roles to showcase on exported resumes.
                    </p>
                  ) : (
                    <ExperienceDisplay entries={experience} />
                  )}
                </CardContent>
              </Card>

              {/* Certifications */}
              <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm">
                <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-slate-100">
                  <div>
                    <CardTitle className="text-base text-slate-900">Certifications</CardTitle>
                    <CardDescription className="text-slate-500">
                      Professional certificates to highlight in your resumes.
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-1 gap-2"
                    onClick={editingCerts ? saveCerts : startEditCerts}
                    disabled={loading}
                  >
                    <Pencil className="size-4" />
                    {editingCerts ? "Save" : "Edit"}
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4 pt-6">
                  {loading ? (
                    <p className="text-sm text-slate-500">Loading certifications…</p>
                  ) : editingCerts ? (
                    <EditableEntriesList entries={certsDraft} setEntries={setCertsDraft} />
                  ) : certifications.length === 0 ? (
                    <p className="text-sm text-slate-500">
                      No certificates added yet. Add some to include them on your resumes.
                    </p>
                  ) : (
                    <EntriesDisplay entries={certifications} emptyMessage="" />
                  )}
                </CardContent>
              </Card>

              {/* Public Portfolio Settings */}
              <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm">
                <CardHeader className="border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <Globe className="size-4 text-slate-500" />
                    <CardTitle className="text-base text-slate-900">Public Portfolio</CardTitle>
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
                          <p className="text-sm font-medium text-slate-800">Portfolio visibility</p>
                          <p className="text-xs text-slate-500">
                            Make your portfolio accessible to anyone with your link.
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
                        <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600 font-mono break-all select-all">
                          {publicUrl}
                        </div>
                      )}

                      <div className="space-y-1.5">
                        <p className="text-sm font-medium text-slate-800">Active resume</p>
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
                    <CardTitle className="text-base text-slate-900">Security</CardTitle>
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
        </div>
      </main>
    </>
  );
}

function ProfileField({
  label,
  value,
  isLink,
}: {
  label: string;
  value: string | null;
  isLink?: boolean;
}) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      {value ? (
        isLink ? (
          <a
            href={value}
            target="_blank"
            rel="noreferrer"
            className="mt-0.5 block text-sm text-indigo-600 hover:underline break-all"
          >
            {value}
          </a>
        ) : (
          <p className="mt-0.5 text-sm text-slate-800 break-words">{value}</p>
        )
      ) : (
        <p className="mt-0.5 text-sm text-slate-400">Not set</p>
      )}
    </div>
  );
}

function EditableEntriesList({
  entries,
  setEntries,
}: {
  entries: EditableEducationEntry[];
  setEntries: (next: EditableEducationEntry[]) => void;
}) {
  function updateEntry(index: number, patch: Partial<EditableEducationEntry>) {
    setEntries(entries.map((e, i) => (i === index ? { ...e, ...patch } : e)));
  }

  function addEntry() {
    setEntries([
      ...entries,
      { title: "", organization: "", date_text: "", description: "" },
    ]);
  }

  return (
    <div className="space-y-4">
      {entries.map((entry, idx) => (
        <div key={idx} className="rounded-lg border border-slate-200 bg-slate-50/60 p-3 space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Title (required)
              </label>
              <Input
                value={entry.title}
                onChange={(e) => updateEntry(idx, { title: e.target.value })}
                placeholder="BSc in Computer Science"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Organization (optional)
              </label>
              <Input
                value={entry.organization ?? ""}
                onChange={(e) => updateEntry(idx, { organization: e.target.value })}
                placeholder="University / Provider"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Dates (display text, optional)
              </label>
              <Input
                value={entry.date_text ?? ""}
                onChange={(e) => updateEntry(idx, { date_text: e.target.value })}
                placeholder="2022 - 2026"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Description (optional)
            </label>
            <Textarea
              rows={2}
              value={entry.description ?? ""}
              onChange={(e) => updateEntry(idx, { description: e.target.value })}
            />
          </div>
        </div>
      ))}
      <Button
        variant="outline"
        size="sm"
        type="button"
        className="mt-1"
        onClick={addEntry}
      >
        Add another
      </Button>
    </div>
  );
}

function EntriesDisplay({
  entries,
  emptyMessage,
}: {
  entries: UserEducationEntry[];
  emptyMessage: string;
}) {
  if (entries.length === 0 && emptyMessage) {
    return <p className="text-sm text-slate-500">{emptyMessage}</p>;
  }
  return (
    <div className="space-y-3">
      {entries.map((e) => (
        <div
          key={e.entry_id}
          className="rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2"
        >
          <p className="text-sm font-medium text-slate-900">{e.title}</p>
          {(e.organization || e.date_text) && (
            <p className="text-xs text-slate-500">
              {[e.organization, e.date_text].filter(Boolean).join(" • ")}
            </p>
          )}
          {e.description && (
            <p className="mt-1 text-sm text-slate-700 whitespace-pre-line">{e.description}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function EditableExperienceList({
  entries,
  setEntries,
}: {
  entries: EditableExperienceEntry[];
  setEntries: (next: EditableExperienceEntry[]) => void;
}) {
  function updateEntry(index: number, patch: Partial<EditableExperienceEntry>) {
    setEntries(entries.map((e, i) => (i === index ? { ...e, ...patch } : e)));
  }

  function addEntry() {
    setEntries([
      ...entries,
      { role: "", company: "", date_text: "", description: "" },
    ]);
  }

  return (
    <div className="space-y-4">
      {entries.map((entry, idx) => (
        <div key={idx} className="rounded-lg border border-slate-200 bg-slate-50/60 p-3 space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Role (required)
              </label>
              <Input
                value={entry.role}
                onChange={(e) => updateEntry(idx, { role: e.target.value })}
                placeholder="Full Stack Engineer"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Company (optional)
              </label>
              <Input
                value={entry.company ?? ""}
                onChange={(e) => updateEntry(idx, { company: e.target.value })}
                placeholder="Company name"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Dates (display text, optional)
              </label>
              <Input
                value={entry.date_text ?? ""}
                onChange={(e) => updateEntry(idx, { date_text: e.target.value })}
                placeholder="Sep 2025 - Dec 2025"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Description (optional)
            </label>
            <Textarea
              rows={2}
              value={entry.description ?? ""}
              onChange={(e) => updateEntry(idx, { description: e.target.value })}
            />
          </div>
        </div>
      ))}
      <Button
        variant="outline"
        size="sm"
        type="button"
        className="mt-1"
        onClick={addEntry}
      >
        Add another
      </Button>
    </div>
  );
}

function ExperienceDisplay({ entries }: { entries: UserExperienceEntry[] }) {
  return (
    <div className="space-y-3">
      {entries.map((e) => (
        <div
          key={e.entry_id}
          className="rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2"
        >
          <p className="text-sm font-medium text-slate-900">{e.role}</p>
          {(e.company || e.date_text) && (
            <p className="text-xs text-slate-500">
              {[e.company, e.date_text].filter(Boolean).join(" • ")}
            </p>
          )}
          {e.description && (
            <p className="mt-1 text-sm text-slate-700 whitespace-pre-line">{e.description}</p>
          )}
        </div>
      ))}
    </div>
  );
}

