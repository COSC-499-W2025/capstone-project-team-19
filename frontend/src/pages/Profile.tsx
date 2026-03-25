import { Fragment, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";
import { tokenStore } from "../auth/token";
import { deleteAccount } from "../api/auth";
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
import { PageContainer, PageHeader } from "../components/shared";

type EditableEducationEntry = Omit<UserEducationEntry, "entry_id" | "entry_type" | "display_order" | "created_at" | "updated_at">;
type EditableExperienceEntry = Omit<UserExperienceEntry, "entry_id" | "display_order" | "created_at" | "updated_at">;

type FieldKind = "input" | "textarea";
type FieldSpec<T extends Record<string, unknown>> = {
  key: keyof T;
  label: string;
  required?: boolean;
  placeholder?: string;
  kind?: FieldKind;
  rows?: number;
  colSpan?: 1 | 2;
};

function ProfileSectionCard({
  title,
  description,
  actionLabel,
  onAction,
  actionDisabled,
  contentClassName,
  headerClassName,
  children,
}: {
  title: ReactNode;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  actionDisabled?: boolean;
  contentClassName?: string;
  headerClassName?: string;
  children: ReactNode;
}) {
  return (
    <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm">
      <CardHeader
        className={[
          "flex flex-row items-start justify-between gap-4 border-b border-slate-100 px-6 py-3",
          headerClassName ?? "",
        ].join(" ")}
      >
        <div>
          <CardTitle className="text-base text-slate-900">{title}</CardTitle>
          {description ? (
            <CardDescription className="text-slate-500">{description}</CardDescription>
          ) : null}
        </div>
        {actionLabel && onAction ? (
          <Button
            variant="outline"
            size="sm"
            className="mt-1 gap-2"
            onClick={onAction}
            disabled={actionDisabled}
          >
            <Pencil className="size-4" />
            {actionLabel}
          </Button>
        ) : null}
      </CardHeader>
      <CardContent className={["space-y-4 pt-2", contentClassName ?? ""].join(" ")}>
        {children}
      </CardContent>
    </Card>
  );
}

function ProfileFormField({
  label,
  value,
  onChange,
  placeholder,
  required,
}: {
  label: string;
  value: string;
  onChange: (next: string) => void;
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-slate-600">
        {label}
        {required ? " (required)" : " (optional)"}
      </label>
      <Input value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

function EditableList<T extends Record<string, any>>({
  entries,
  setEntries,
  emptyRow,
  fields,
  addLabel = "Add another",
  requiredKey,
}: {
  entries: T[];
  setEntries: (next: T[]) => void;
  emptyRow: T;
  fields: Array<FieldSpec<T>>;
  addLabel?: string;
  requiredKey: keyof T;
}) {
  const gridFields = fields.filter((f) => (f.kind ?? "input") === "input");
  const textareaFields = fields.filter((f) => (f.kind ?? "input") === "textarea");

  function updateEntry(index: number, key: keyof T, value: string) {
    setEntries(entries.map((e, i) => (i === index ? { ...e, [key]: value } : e)));
  }

  function addEntry() {
    setEntries([...entries, { ...emptyRow }]);
  }

  function removeEntry(index: number) {
    setEntries(entries.filter((_, i) => i !== index));
  }

  return (
    <div className="space-y-4">
      {entries.map((entry, idx) => {
        const canRemove = entries.length > 1 || String(entry[requiredKey] ?? "").trim() !== "";
        return (
          <div
            key={idx}
            className="rounded-lg border border-slate-200 bg-slate-50/60 p-3 space-y-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="w-full space-y-3">
                {gridFields.length ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {gridFields.map((f) => (
                      <div key={String(f.key)} className={f.colSpan === 2 ? "sm:col-span-2" : ""}>
                        <label className="mb-1 block text-xs font-medium text-slate-600">
                          {f.label}
                          {f.required ? " (required)" : " (optional)"}
                        </label>
                        <Input
                          value={String(entry[f.key] ?? "")}
                          placeholder={f.placeholder}
                          onChange={(e) => updateEntry(idx, f.key, e.target.value)}
                        />
                      </div>
                    ))}
                  </div>
                ) : null}

                {textareaFields.map((f) => (
                  <div key={String(f.key)}>
                    <label className="mb-1 block text-xs font-medium text-slate-600">
                      {f.label}
                      {f.required ? " (required)" : " (optional)"}
                    </label>
                    <Textarea
                      rows={f.rows ?? 2}
                      value={String(entry[f.key] ?? "")}
                      placeholder={f.placeholder}
                      onChange={(e) => updateEntry(idx, f.key, e.target.value)}
                    />
                  </div>
                ))}
              </div>

              {canRemove ? (
                <Button
                  variant="ghost"
                  size="sm"
                  type="button"
                  className="text-slate-500 hover:text-slate-900"
                  onClick={() => removeEntry(idx)}
                  aria-label="Remove entry"
                >
                  ✕
                </Button>
              ) : null}
            </div>
          </div>
        );
      })}
      <Button variant="outline" size="sm" type="button" className="mt-1" onClick={addEntry}>
        {addLabel}
      </Button>
    </div>
  );
}

function EntryListDisplay<T extends Record<string, any>>({
  entries,
  titleKey,
  metaKeys,
  descriptionKey,
  keyField,
}: {
  entries: T[];
  titleKey: keyof T;
  metaKeys: Array<keyof T>;
  descriptionKey?: keyof T;
  keyField: keyof T;
}) {
  return (
    <div className="space-y-3">
      {entries.map((e) => {
        const meta = metaKeys.map((k) => e[k]).filter(Boolean).join(" • ");
        const desc = descriptionKey ? (e[descriptionKey] as unknown as string | null) : null;
        return (
          <div
            key={String(e[keyField])}
            className="rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2"
          >
            <p className="text-sm font-medium text-slate-900">{String(e[titleKey] ?? "")}</p>
            {meta ? <p className="text-xs text-slate-500">{meta}</p> : null}
            {desc ? <p className="mt-1 text-sm text-slate-700 whitespace-pre-line">{desc}</p> : null}
          </div>
        );
      })}
    </div>
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

  function startEditList<TSource, TDraft>({
    sourceEntries,
    pickDraft,
    emptyRow,
    setDraft,
    setEditing,
  }: {
    sourceEntries: TSource[];
    pickDraft: (e: TSource) => TDraft;
    emptyRow: TDraft;
    setDraft: (next: TDraft[]) => void;
    setEditing: (next: boolean) => void;
  }) {
    const initial = sourceEntries.map(pickDraft);
    setDraft(initial.length === 0 ? [{ ...emptyRow }] : initial);
    setEditing(true);
  }

  async function saveList<TDraft, TList>({
    draftEntries,
    requiredKey,
    replaceFn,
    setList,
    setEditing,
  }: {
    draftEntries: TDraft[];
    requiredKey: keyof TDraft;
    replaceFn: (payload: { entries: TDraft[] }) => Promise<{ entries: TList[] }>;
    setList: (next: TList[]) => void;
    setEditing: (next: boolean) => void;
  }) {
    try {
      const cleaned = draftEntries.filter((e) => String(e[requiredKey] ?? "").trim() !== "");
      const updated = await replaceFn({ entries: cleaned });
      setList(updated.entries);
      setEditing(false);
    } catch {
      // ignore for now
    }
  }

  const educationFields = useMemo<Array<FieldSpec<EditableEducationEntry>>>(
    () => [
      { key: "title", label: "Title", required: true, placeholder: "BSc in Computer Science" },
      { key: "organization", label: "Organization", placeholder: "University / Provider" },
      { key: "date_text", label: "Dates (display text)", placeholder: "2022 - 2026" },
      { key: "description", label: "Description", kind: "textarea", rows: 2 },
    ],
    [],
  );

  const experienceFields = useMemo<Array<FieldSpec<EditableExperienceEntry>>>(
    () => [
      { key: "role", label: "Role", required: true, placeholder: "Full Stack Engineer" },
      { key: "company", label: "Company", placeholder: "Company name" },
      { key: "date_text", label: "Dates (display text)", placeholder: "Sep 2025 - Dec 2025" },
      { key: "description", label: "Description", kind: "textarea", rows: 2 },
    ],
    [],
  );

  useEffect(() => {
    setLoading(true);
    setSettingsLoading(true);
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
      .finally(() => {
        setLoading(false);
        setSettingsLoading(false);
      });
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
    } catch {
      // ignore for now
    }
  }

  function startEditEducation() {
    startEditList<UserEducationEntry, EditableEducationEntry>({
      sourceEntries: education,
      pickDraft: (e) => ({
        title: e.title,
        organization: e.organization,
        date_text: e.date_text,
        description: e.description,
      }),
      emptyRow: { title: "", organization: "", date_text: "", description: "" },
      setDraft: setEducationDraft,
      setEditing: setEditingEducation,
    });
  }

  async function saveEducation() {
    await saveList<EditableEducationEntry, UserEducationEntry>({
      draftEntries: educationDraft,
      requiredKey: "title",
      replaceFn: replaceEducation,
      setList: setEducation,
      setEditing: setEditingEducation,
    });
  }

  function startEditCerts() {
    startEditList<UserEducationEntry, EditableEducationEntry>({
      sourceEntries: certifications,
      pickDraft: (e) => ({
        title: e.title,
        organization: e.organization,
        date_text: e.date_text,
        description: e.description,
      }),
      emptyRow: { title: "", organization: "", date_text: "", description: "" },
      setDraft: setCertsDraft,
      setEditing: setEditingCerts,
    });
  }

  async function saveCerts() {
    await saveList<EditableEducationEntry, UserEducationEntry>({
      draftEntries: certsDraft,
      requiredKey: "title",
      replaceFn: replaceCertifications,
      setList: setCertifications,
      setEditing: setEditingCerts,
    });
  }

  function startEditExperience() {
    startEditList<UserExperienceEntry, EditableExperienceEntry>({
      sourceEntries: experience,
      pickDraft: (e) => ({
        role: e.role,
        company: e.company,
        date_text: e.date_text,
        description: e.description,
      }),
      emptyRow: { role: "", company: "", date_text: "", description: "" },
      setDraft: setExperienceDraft,
      setEditing: setEditingExperience,
    });
  }

  async function saveExperience() {
    await saveList<EditableExperienceEntry, UserExperienceEntry>({
      draftEntries: experienceDraft,
      requiredKey: "role",
      replaceFn: replaceExperience,
      setList: setExperience,
      setEditing: setEditingExperience,
    });
  }

  function startEditSummary() {
    if (!profile) return;
    setSummaryDraft(profile.profile_text ?? "");
    setEditingSummary(true);
  }

  async function saveSummary() {
    if (!profile) return;
    try {
      const updated = await updateProfile({ profile_text: summaryDraft });
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
        value === "" ? { clear_active_resume: true } : { active_resume_id: Number(value) }
      );
      setSettings(updated);
    } finally {
      setSaving(false);
    }
  }

  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDeleteAccount() {
    setDeleting(true);
    try {
      await deleteAccount();
      tokenStore.clear();
      window.location.replace("/login");
    } catch {
      setDeleting(false);
      setConfirmingDelete(false);
    }
  }

  const publicUrl = `${window.location.origin}/public/${username}/projects`;

  return (
    <>
      <TopBar showNav username={username} />

      <PageContainer className="min-h-[calc(100vh-56px)] bg-background pt-[12px]">
        <PageHeader
          title="Profile"
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "Profile" },
          ]}
        />

        <div className="grid gap-8 lg:grid-cols-[320px_1fr]">
          <aside className="lg:self-start">
            <ProfileSectionCard
              title={`@${username}`}
              actionLabel={editingProfile ? "Save" : "Edit"}
              onAction={editingProfile ? saveProfile : startEditProfile}
              actionDisabled={loading || (!profile && !editingProfile)}
            >
              {loading || !profile ? (
                <p className="text-sm text-slate-500">Loading profile…</p>
              ) : editingProfile ? (
                <div className="space-y-3">
                  <ProfileFormField
                    label="Full name"
                    value={profileDraft.full_name ?? profile.full_name ?? ""}
                    onChange={(v) => setProfileDraft((d) => ({ ...d, full_name: v }))}
                  />
                  <ProfileFormField
                    label="Email"
                    value={profileDraft.email ?? profile.email ?? ""}
                    onChange={(v) => setProfileDraft((d) => ({ ...d, email: v }))}
                  />
                  <ProfileFormField
                    label="Phone"
                    value={profileDraft.phone ?? profile.phone ?? ""}
                    onChange={(v) => setProfileDraft((d) => ({ ...d, phone: v }))}
                  />
                  <ProfileFormField
                    label="Location"
                    value={profileDraft.location ?? profile.location ?? ""}
                    onChange={(v) => setProfileDraft((d) => ({ ...d, location: v }))}
                  />
                  <ProfileFormField
                    label="LinkedIn URL"
                    value={profileDraft.linkedin ?? profile.linkedin ?? ""}
                    onChange={(v) => setProfileDraft((d) => ({ ...d, linkedin: v }))}
                  />
                  <ProfileFormField
                    label="GitHub URL"
                    value={profileDraft.github ?? profile.github ?? ""}
                    onChange={(v) => setProfileDraft((d) => ({ ...d, github: v }))}
                  />
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
            </ProfileSectionCard>
          </aside>

          <section className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold tracking-tight text-slate-900">Profile overview</h2>
              <p className="mt-1 text-sm text-slate-500">
                Manage the information that appears on your resumes and portfolio, plus your account security.
              </p>
            </div>

            <ProfileSectionCard
              title="Profile summary"
              description="A short paragraph that appears at the top of your resumes."
              actionLabel={editingSummary ? "Save" : "Edit"}
              onAction={editingSummary ? saveSummary : startEditSummary}
              actionDisabled={loading || (!profile && !editingSummary)}
            >
              {loading || !profile ? (
                <p className="text-sm text-slate-500">Loading profile…</p>
              ) : editingSummary ? (
                <Textarea
                  rows={4}
                  value={summaryDraft}
                  onChange={(e) => setSummaryDraft(e.target.value)}
                />
              ) : (
                <p className="text-sm text-slate-700 whitespace-pre-line">
                  {profile.profile_text || "Not added yet."}
                </p>
              )}
            </ProfileSectionCard>

            <ProfileSectionCard
              title="Education"
              description="Degrees and academic programs to include on your resumes."
              actionLabel={editingEducation ? "Save" : "Edit"}
              onAction={editingEducation ? saveEducation : startEditEducation}
              actionDisabled={loading}
            >
              {loading ? (
                <p className="text-sm text-slate-500">Loading education…</p>
              ) : editingEducation ? (
                <EditableList
                  entries={educationDraft}
                  setEntries={setEducationDraft}
                  emptyRow={{ title: "", organization: "", date_text: "", description: "" }}
                  fields={educationFields}
                  requiredKey="title"
                />
              ) : education.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No education added yet. Add entries to show your degrees and programs on exported resumes.
                </p>
              ) : (
                <EntryListDisplay
                  entries={education}
                  titleKey="title"
                  metaKeys={["organization", "date_text"]}
                  descriptionKey="description"
                  keyField="entry_id"
                />
              )}
            </ProfileSectionCard>

            <ProfileSectionCard
              title="Experience"
              description="Work experience and internships to include on your resumes."
              actionLabel={editingExperience ? "Save" : "Edit"}
              onAction={editingExperience ? saveExperience : startEditExperience}
              actionDisabled={loading}
            >
              {loading ? (
                <p className="text-sm text-slate-500">Loading experience…</p>
              ) : editingExperience ? (
                <EditableList
                  entries={experienceDraft}
                  setEntries={setExperienceDraft}
                  emptyRow={{ role: "", company: "", date_text: "", description: "" }}
                  fields={experienceFields}
                  requiredKey="role"
                />
              ) : experience.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No experience added yet. Add roles to showcase on exported resumes.
                </p>
              ) : (
                <EntryListDisplay
                  entries={experience}
                  titleKey="role"
                  metaKeys={["company", "date_text"]}
                  descriptionKey="description"
                  keyField="entry_id"
                />
              )}
            </ProfileSectionCard>

            <ProfileSectionCard
              title="Certifications"
              description="Professional certificates to highlight in your resumes."
              actionLabel={editingCerts ? "Save" : "Edit"}
              onAction={editingCerts ? saveCerts : startEditCerts}
              actionDisabled={loading}
            >
              {loading ? (
                <p className="text-sm text-slate-500">Loading certifications…</p>
              ) : editingCerts ? (
                <EditableList
                  entries={certsDraft}
                  setEntries={setCertsDraft}
                  emptyRow={{ title: "", organization: "", date_text: "", description: "" }}
                  fields={educationFields}
                  requiredKey="title"
                />
              ) : certifications.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No certificates added yet. Add some to include them on your resumes.
                </p>
              ) : (
                <EntryListDisplay
                  entries={certifications}
                  titleKey="title"
                  metaKeys={["organization", "date_text"]}
                  descriptionKey="description"
                  keyField="entry_id"
                />
              )}
            </ProfileSectionCard>

            <ProfileSectionCard
              title={
                <span className="inline-flex items-center gap-2">
                  <Globe className="size-4 text-slate-500" />
                  Public Portfolio
                </span>
              }
              description="Control what visitors see at your public portfolio URL."
              contentClassName="space-y-5"
              headerClassName="items-center"
            >
              {settingsLoading ? (
                <p className="text-sm text-slate-500">Loading…</p>
              ) : (
                <Fragment>
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
                    <div className="break-all rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-xs text-slate-600 select-all">
                      {publicUrl}
                    </div>
                  )}

                  <div className="space-y-1.5">
                    <p className="text-sm font-medium text-slate-800">Active resume</p>
                    <p className="text-xs text-slate-500">The resume shown on your public portfolio.</p>
                    <select
                      value={settings.active_resume_id ?? ""}
                      onChange={handleResumeChange}
                      disabled={saving}
                      className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 disabled:opacity-60"
                    >
                      <option value="">— None —</option>
                      {resumes.map((r) => (
                        <option key={r.id} value={r.id}>{r.name}</option>
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
                </Fragment>
              )}
            </ProfileSectionCard>

            <ProfileSectionCard
              title={
                <span className="inline-flex items-center gap-2">
                  <ShieldCheck className="size-4 text-slate-500" />
                  Security
                </span>
              }
              description="Password and account controls (placeholder actions for now)."
              contentClassName="space-y-3"
              headerClassName="items-center"
            >
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

              {confirmingDelete ? (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 space-y-3">
                  <p className="text-sm text-red-700">
                    Are you sure? This will permanently delete your account and all your data. This action cannot be undone.
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleDeleteAccount}
                      disabled={deleting}
                    >
                      {deleting ? "Deleting..." : "Yes, delete my account"}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setConfirmingDelete(false)}
                      disabled={deleting}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <Button
                  variant="ghost"
                  size="default"
                  className="h-11 w-full justify-start gap-3 text-red-600 hover:bg-red-50 hover:text-red-700"
                  type="button"
                  onClick={() => setConfirmingDelete(true)}
                >
                  <Trash2 className="size-4" />
                  Delete account
                </Button>
              )}
            </ProfileSectionCard>
          </section>
        </div>
      </PageContainer>
    </>
  );
}