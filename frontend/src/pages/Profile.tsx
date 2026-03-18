import { useEffect, useState } from "react";
import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { KeyRound, LogOut, Pencil, ShieldCheck, Trash2 } from "lucide-react";
import {
  getProfile,
  updateProfile,
  getEducation,
  replaceEducation,
  getCertifications,
  replaceCertifications,
  type UserProfile,
  type UserEducationEntry,
} from "../api/profile";

type EditableEducationEntry = Omit<UserEducationEntry, "entry_id" | "entry_type" | "display_order" | "created_at" | "updated_at">;

export default function ProfilePage() {
  const username = getUsername();
  const displayName = username;
  const initials = displayName.slice(0, 1).toUpperCase();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [education, setEducation] = useState<UserEducationEntry[]>([]);
  const [certifications, setCertifications] = useState<UserEducationEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const [editingProfile, setEditingProfile] = useState(false);
  const [editingEducation, setEditingEducation] = useState(false);
  const [editingCerts, setEditingCerts] = useState(false);

  const [profileDraft, setProfileDraft] = useState<Partial<UserProfile>>({});
  const [educationDraft, setEducationDraft] = useState<EditableEducationEntry[]>([]);
  const [certsDraft, setCertsDraft] = useState<EditableEducationEntry[]>([]);

  useEffect(() => {
    setLoading(true);
    Promise.all([getProfile(), getEducation(), getCertifications()])
      .then(([p, edu, certs]) => {
        setProfile(p);
        setEducation(edu.entries);
        setCertifications(certs.entries);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
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
        profile_text: profileDraft.profile_text ?? profile.profile_text ?? "",
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

  return (
    <>
      <TopBar showNav username={username} />
      <main className="min-h-[calc(100vh-56px)] bg-gradient-to-b from-slate-50 via-white to-slate-100/40">
        <div className="mx-auto w-full max-w-6xl px-6 py-10">
          <div className="grid gap-8 lg:grid-cols-[320px_1fr]">
            <aside className="lg:sticky lg:top-24 lg:self-start">
              <Card className="rounded-2xl border-slate-200/80 bg-white shadow-sm">
                <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-slate-100">
                  <div className="flex items-center gap-4">
                    <Avatar className="h-16 w-16 border border-slate-200 text-xl">
                      <AvatarFallback className="bg-slate-100 font-semibold text-slate-800">
                        {initials}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h1 className="text-lg font-semibold tracking-tight text-slate-900">
                        {displayName}
                      </h1>
                      <p className="text-sm text-slate-500">@{username}</p>
                    </div>
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
                      <div>
                        <label className="mb-1 block text-xs font-medium text-slate-600">
                          Profile summary
                        </label>
                        <Textarea
                          rows={4}
                          value={profileDraft.profile_text ?? profile.profile_text ?? ""}
                          onChange={(e) =>
                            setProfileDraft((d) => ({ ...d, profile_text: e.target.value }))
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
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                          Profile summary
                        </p>
                        <p className="mt-1 text-sm text-slate-700 whitespace-pre-line">
                          {profile.profile_text || "Not added yet."}
                        </p>
                      </div>
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
              <label className="mb-1 block text-xs font-medium text-slate-600">Title</label>
              <Input
                value={entry.title}
                onChange={(e) => updateEntry(idx, { title: e.target.value })}
                placeholder="BSc in Computer Science"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Organization
              </label>
              <Input
                value={entry.organization ?? ""}
                onChange={(e) => updateEntry(idx, { organization: e.target.value })}
                placeholder="University / Provider"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Dates (display text)
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

