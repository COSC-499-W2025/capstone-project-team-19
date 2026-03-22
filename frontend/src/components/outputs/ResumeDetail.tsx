import { useEffect, useState } from "react";
import {
  getResume,
  editResume,
  removeProjectFromResume,
  downloadResumeDocx,
  downloadResumePdf,
  type ResumeDetail as ResumeDetailType,
  type ResumeProject,
} from "../../api/outputs";
import { MinimalConfirmDialog } from "../shared";
import ExportDropdown from "./ExportDropdown";
import AddProjectModal from "./AddProjectModal";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardAction,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  Pencil,
  Check,
  X,
  Plus,
  Trash2,
} from "lucide-react";

type Props = {
  resumeId: number;
  initialEditing?: boolean;
  onBack: () => void;
};

type ProjectEdits = {
  display_name: string;
  summary_text: string;
  key_role: string;
  contribution_bullets: string[];
  scope: "resume_only" | "global";
};

export default function ResumeDetail({
  resumeId,
  initialEditing = false,
  onBack,
}: Props) {
  const [resume, setResume] = useState<ResumeDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  // Edit mode toggle
  const [editing, setEditing] = useState(initialEditing);

  // Resume name editing
  const [editingName, setEditingName] = useState(false);
  const [nameVal, setNameVal] = useState("");
  const [savingName, setSavingName] = useState(false);

  // Per-project editing
  const [editingProjectId, setEditingProjectId] = useState<number | null>(null);
  const [projectEdits, setProjectEdits] = useState<ProjectEdits | null>(null);
  const [savingProject, setSavingProject] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [projectToRemove, setProjectToRemove] = useState<ResumeProject | null>(
    null
  );
  const [removingProject, setRemovingProject] = useState(false);
  const [showAddProject, setShowAddProject] = useState(false);

  function loadResume() {
    setLoading(true);
    setErr(null);
    getResume(resumeId)
      .then((r) => {
        setResume(r.data);
        setNameVal(r.data?.name ?? "");
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(loadResume, [resumeId]);

  // Clear success message after 3 seconds
  useEffect(() => {
    if (!successMsg) return;
    const t = setTimeout(() => setSuccessMsg(null), 3000);
    return () => clearTimeout(t);
  }, [successMsg]);

  // When leaving edit mode, collapse any open project edit
  function toggleEditing() {
    if (editing) {
      setEditingProjectId(null);
      setProjectEdits(null);
      setEditingName(false);
      setNameVal(resume?.name ?? "");
    }
    setEditing(!editing);
  }

  /* ── Export ── */
  async function handleExportDocx() {
    try {
      await downloadResumeDocx(resumeId);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function handleExportPdf() {
    try {
      await downloadResumePdf(resumeId);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  /* ── Resume name save ── */
  async function handleSaveName() {
    if (!nameVal.trim() || nameVal === resume?.name) {
      setEditingName(false);
      return;
    }
    setSavingName(true);
    setErr(null);
    try {
      await editResume(resumeId, { name: nameVal.trim() });
      setResume((r) => (r ? { ...r, name: nameVal.trim() } : r));
      setEditingName(false);
      setSuccessMsg("Resume name updated");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setSavingName(false);
    }
  }

  /* ── Open project edit ── */
  function startEditingProject(p: ResumeProject) {
    if (p.project_summary_id == null) return;
    setEditingProjectId(p.project_summary_id);
    setProjectEdits({
      display_name: p.project_name,
      summary_text: p.summary_text ?? "",
      key_role: p.key_role ?? "",
      contribution_bullets: [...p.contribution_bullets],
      scope: "resume_only",
    });
    setErr(null);
  }

  function cancelEditingProject() {
    setEditingProjectId(null);
    setProjectEdits(null);
  }

  /* ── Save project edits ── */
  async function handleSaveProject() {
    if (!projectEdits || editingProjectId == null) return;
    setSavingProject(true);
    setErr(null);
    try {
      const payload: Record<string, unknown> = {
        project_summary_id: editingProjectId,
        scope: projectEdits.scope,
      };
      const original = resume?.projects.find(
        (p) => p.project_summary_id === editingProjectId
      );
      if (original) {
        if (projectEdits.display_name !== original.project_name) {
          payload.display_name = projectEdits.display_name;
        }
        if (projectEdits.summary_text !== (original.summary_text ?? "")) {
          payload.summary_text = projectEdits.summary_text;
        }
        if (projectEdits.key_role !== (original.key_role ?? "")) {
          payload.key_role = projectEdits.key_role;
        }
        const bulletsChanged =
          JSON.stringify(projectEdits.contribution_bullets) !==
          JSON.stringify(original.contribution_bullets);
        if (bulletsChanged) {
          payload.contribution_bullets = projectEdits.contribution_bullets;
          payload.contribution_edit_mode = "replace";
        }
      }

      const fieldKeys = Object.keys(payload).filter(
        (k) => k !== "project_summary_id" && k !== "scope"
      );
      if (fieldKeys.length === 0) {
        cancelEditingProject();
        return;
      }

      await editResume(resumeId, payload as any);
      setEditingProjectId(null);
      setProjectEdits(null);
      setSuccessMsg(
        projectEdits.scope === "global"
          ? "Updated across all resumes"
          : "Updated this resume"
      );
      loadResume();
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setSavingProject(false);
    }
  }

  /* ── Bullet helpers ── */
  function updateBullet(index: number, value: string) {
    if (!projectEdits) return;
    const bullets = [...projectEdits.contribution_bullets];
    bullets[index] = value;
    setProjectEdits({ ...projectEdits, contribution_bullets: bullets });
  }

  function removeBullet(index: number) {
    if (!projectEdits) return;
    const bullets = projectEdits.contribution_bullets.filter(
      (_, i) => i !== index
    );
    setProjectEdits({ ...projectEdits, contribution_bullets: bullets });
  }

  function addBullet() {
    if (!projectEdits) return;
    setProjectEdits({
      ...projectEdits,
      contribution_bullets: [...projectEdits.contribution_bullets, ""],
    });
  }

  /* ── Remove project from resume ── */
  async function handleRemoveProject() {
    if (!projectToRemove) return;
    setRemovingProject(true);
    setErr(null);
    try {
      const res = await removeProjectFromResume(resumeId, projectToRemove.project_name);
      setProjectToRemove(null);
      if (res.data) {
        setResume(res.data);
        setSuccessMsg("Project removed from resume");
      } else {
        onBack();
      }
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setRemovingProject(false);
    }
  }

  /* ── Render ── */
  if (loading)
    return (
      <div className="content">
        <p>Loading...</p>
      </div>
    );
  if (err && !resume)
    return (
      <div className="content">
        <p className="error">{err}</p>
      </div>
    );
  if (!resume)
    return (
      <div className="content">
        <p>Resume not found.</p>
      </div>
    );

  const sortedProjects = sortProjectsByDate(resume.projects);
  const agg = resume.aggregated_skills;

  return (
    <div className="content">
      {/* Header */}
      <div className="outputsHeader">
        <button className="backBtn" onClick={onBack}>
          &larr;
        </button>

        {editing && editingName ? (
          <div className="flex items-center gap-2" style={{ flex: 1 }}>
            <Input
              value={nameVal}
              onChange={(e) => setNameVal(e.target.value)}
              className="max-w-xs text-lg font-semibold"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSaveName();
                if (e.key === "Escape") {
                  setEditingName(false);
                  setNameVal(resume.name);
                }
              }}
            />
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={handleSaveName}
              disabled={savingName}
            >
              <Check className="size-4 text-emerald-600" />
            </Button>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => {
                setEditingName(false);
                setNameVal(resume.name);
              }}
            >
              <X className="size-4 text-slate-400" />
            </Button>
          </div>
        ) : (
          <>
            <h2>
              {resume.name}
              {editing && (
                <Button
                  variant="ghost"
                  size="icon-xs"
                  className="ml-2 align-middle"
                  onClick={() => setEditingName(true)}
                >
                  <Pencil className="size-3.5 text-slate-400" />
                </Button>
              )}
            </h2>
          </>
        )}

        {editing && (
          <button
            className="actionBtn outline"
            onClick={() => setShowAddProject(true)}
          >
            Add Project
          </button>
        )}
        <button
          className={`actionBtn ${editing ? "dark" : "outline"}`}
          onClick={toggleEditing}
        >
          {editing ? "Done Editing" : "Edit"}
        </button>
        {!editing && (
          <ExportDropdown onDocx={handleExportDocx} onPdf={handleExportPdf} />
        )}
      </div>

      <hr className="divider" />

      {/* Success / Error banners */}
      {successMsg && (
        <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-700">
          {successMsg}
        </div>
      )}
      {err && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600">
          {err}
        </div>
      )}

      {/* Skills Summary */}
      {editing ? (
        <Card className="mb-6 rounded-2xl border-slate-200/80 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="text-base text-slate-900">
              Skills
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <SkillRow label="Languages" items={agg.languages} />
            <SkillRow label="Frameworks" items={agg.frameworks} />
            <SkillRow label="Technical" items={agg.technical_skills} />
            <SkillRow label="Writing" items={agg.writing_skills} />
          </CardContent>
        </Card>
      ) : (
        <div className="skillsSummaryBlock">
          <h3>Skills</h3>
          {agg.languages.length > 0 && (
            <p>
              <strong>Languages:</strong> {agg.languages.join(", ")}
            </p>
          )}
          {agg.frameworks.length > 0 && (
            <p>
              <strong>Frameworks:</strong> {agg.frameworks.join(", ")}
            </p>
          )}
          {agg.technical_skills.length > 0 && (
            <p>
              <strong>Technical skills:</strong>{" "}
              {agg.technical_skills.join(", ")}
            </p>
          )}
          {agg.writing_skills.length > 0 && (
            <p>
              <strong>Writing skills:</strong> {agg.writing_skills.join(", ")}
            </p>
          )}
        </div>
      )}

      {/* Projects */}
      {editing ? (
        /* ── Edit mode: shadcn cards with pencil icons ── */
        <div className="space-y-4">
          {resume.projects.map((p) => {
            const isEditingProject =
              editingProjectId === p.project_summary_id;

            return (
              <Card
                key={p.project_summary_id ?? p.project_name}
                className="rounded-2xl border-slate-200/80 bg-white shadow-sm"
              >
                <CardHeader className="border-b border-slate-100">
                  <div>
                    <CardTitle className="text-base text-slate-900">
                      {isEditingProject
                        ? "Editing project"
                        : p.project_name}
                    </CardTitle>
                    <div className="mt-1 flex gap-1.5">
                      {p.project_type && (
                        <Badge variant="secondary" className="text-xs">
                          {p.project_type}
                        </Badge>
                      )}
                      {p.project_mode && (
                        <Badge variant="outline" className="text-xs">
                          {p.project_mode}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <CardAction>
                    {!isEditingProject && (
                      <div className="flex items-center gap-1">
                        {p.project_summary_id != null && (
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => startEditingProject(p)}
                            title="Edit project"
                          >
                            <Pencil className="size-4 text-slate-500" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => setProjectToRemove(p)}
                          title="Remove from resume"
                          className="text-slate-400 hover:text-red-500"
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                    )}
                  </CardAction>
                </CardHeader>

                <CardContent>
                  {isEditingProject && projectEdits ? (
                    <ProjectEditForm
                      edits={projectEdits}
                      setEdits={setProjectEdits}
                      onSave={handleSaveProject}
                      onCancel={cancelEditingProject}
                      saving={savingProject}
                      updateBullet={updateBullet}
                      removeBullet={removeBullet}
                      addBullet={addBullet}
                    />
                  ) : (
                    <ProjectReadView project={p} />
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        /* ── View mode: flat list matching export structure ── */
        <div className="resumeProjectsList">
          <h3 className="groupHeader">Projects</h3>
          {sortedProjects.map((p, i) => (
            <div key={i} className="resumeProjectBlock">
              <ProjectBlockView project={p} />
            </div>
          ))}
        </div>
      )}

      {showAddProject && resume && (
        <AddProjectModal
          resumeId={resumeId}
          currentProjectNames={resume.projects.map((p) => p.project_name)}
          onClose={() => setShowAddProject(false)}
          onAdded={() => {
            loadResume();
            setSuccessMsg("Project added to resume");
          }}
        />
      )}

      <MinimalConfirmDialog
        open={projectToRemove != null}
        onOpenChange={(open) => !open && setProjectToRemove(null)}
        message={
          resume.projects.length <= 1
            ? "If you remove all projects, this resume will be deleted. Continue?"
            : `Remove "${projectToRemove?.project_name}" from this resume?`
        }
        confirmLabel={
          removingProject
            ? "Removing…"
            : resume.projects.length <= 1
              ? "Continue"
              : "Remove"
        }
        onConfirm={handleRemoveProject}
      />
    </div>
  );
}

/* ── Helper functions ── */

function sortProjectsByDate(projects: ResumeProject[]): ResumeProject[] {
  return [...projects].sort((a, b) => {
    const dateA = a.end_date || a.start_date || "";
    const dateB = b.end_date || b.start_date || "";
    // Most recent first; projects with no dates go last
    if (!dateA && !dateB) return 0;
    if (!dateA) return 1;
    if (!dateB) return -1;
    return dateB.localeCompare(dateA);
  });
}

function formatDateRange(start: string | null, end: string | null): string {
  const fmt = (iso: string) => {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return "";
    return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
  };
  const s = start ? fmt(start) : "";
  const e = end ? fmt(end) : "";
  if (s && e) return `${s} \u2013 ${e}`;
  if (s) return `${s} \u2013 Present`;
  if (e) return e;
  return "";
}

/* ── Sub-components ── */

function SkillRow({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <p className="text-sm text-slate-700">
      <span className="font-medium">{label}:</span> {items.join(", ")}
    </p>
  );
}

/** View-mode project block matching export structure: name, role | dates, bullets */
function ProjectBlockView({ project: p }: { project: ResumeProject }) {
  const dateLine = formatDateRange(p.start_date, p.end_date);
  const role = p.key_role || "";
  const subtitle = role && dateLine
    ? `${role} | ${dateLine}`
    : role || dateLine;

  return (
    <div className="projectBlockContent">
      <h4 className="projectBlockName">{p.project_name}</h4>

      {subtitle && (
        <p className="projectField" style={{ fontStyle: "italic" }}>
          {subtitle}
        </p>
      )}

      {p.contribution_bullets.length > 0 && (
        <ul className="bulletList">
          {p.contribution_bullets.map((b, j) => (
            <li key={j}>{b}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Edit-mode project read view (shadcn styled, shown when not actively editing this project) */
function ProjectReadView({ project: p }: { project: ResumeProject }) {
  return (
    <div className="space-y-2 text-sm text-slate-700">
      {p.key_role && (
        <p>
          <span className="font-medium text-slate-900">Role:</span>{" "}
          {p.key_role}
        </p>
      )}
      {p.languages.length > 0 && (
        <p>
          <span className="font-medium text-slate-900">Languages:</span>{" "}
          {p.languages.join(", ")}
        </p>
      )}
      {p.frameworks.length > 0 && (
        <p>
          <span className="font-medium text-slate-900">Frameworks:</span>{" "}
          {p.frameworks.join(", ")}
        </p>
      )}
      {p.summary_text && (
        <p>
          <span className="font-medium text-slate-900">Summary:</span>{" "}
          {p.summary_text}
        </p>
      )}
      {p.contribution_bullets.length > 0 && (
        <div>
          <p className="font-medium text-slate-900">Contributions:</p>
          <ul className="mt-1 list-disc pl-5 space-y-0.5">
            {p.contribution_bullets.map((b, j) => (
              <li key={j}>{b}</li>
            ))}
          </ul>
        </div>
      )}
      {p.skills.length > 0 && (
        <div className="flex flex-wrap gap-1 pt-1">
          {p.skills.map((s) => (
            <Badge key={s} variant="secondary" className="text-xs">
              {s}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

/** Edit form for a single project */
function ProjectEditForm({
  edits,
  setEdits,
  onSave,
  onCancel,
  saving,
  updateBullet,
  removeBullet,
  addBullet,
}: {
  edits: ProjectEdits;
  setEdits: (e: ProjectEdits) => void;
  onSave: () => void;
  onCancel: () => void;
  saving: boolean;
  updateBullet: (i: number, v: string) => void;
  removeBullet: (i: number) => void;
  addBullet: () => void;
}) {
  return (
    <div className="space-y-5">
      <div className="space-y-1.5">
        <Label htmlFor="edit-display-name">Display Name</Label>
        <Input
          id="edit-display-name"
          value={edits.display_name}
          onChange={(e) =>
            setEdits({ ...edits, display_name: e.target.value })
          }
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="edit-key-role">Key Role</Label>
        <Input
          id="edit-key-role"
          placeholder="e.g. Backend Developer"
          value={edits.key_role}
          onChange={(e) => setEdits({ ...edits, key_role: e.target.value })}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="edit-summary">Summary</Label>
        <Textarea
          id="edit-summary"
          rows={3}
          value={edits.summary_text}
          onChange={(e) =>
            setEdits({ ...edits, summary_text: e.target.value })
          }
        />
      </div>

      <div className="space-y-2">
        <Label>Contribution Bullets</Label>

        <div className="space-y-2">
          {edits.contribution_bullets.map((bullet, i) => (
            <div key={i} className="flex items-start gap-2">
              <span className="mt-2.5 text-xs text-slate-400">{i + 1}.</span>
              <Textarea
                rows={2}
                value={bullet}
                onChange={(e) => updateBullet(i, e.target.value)}
                className="flex-1"
              />
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={() => removeBullet(i)}
                className="mt-1 text-slate-400 hover:text-red-500"
              >
                <Trash2 className="size-3.5" />
              </Button>
            </div>
          ))}
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={addBullet}
          className="gap-1.5 text-xs"
        >
          <Plus className="size-3" />
          Add bullet
        </Button>
      </div>

      <Separator />

      <div className="space-y-2">
        <Label>Apply changes to</Label>
        <RadioGroup
          value={edits.scope}
          onValueChange={(v) =>
            setEdits({ ...edits, scope: v as "resume_only" | "global" })
          }
          className="flex flex-col gap-2"
        >
          <div className="flex items-center gap-2">
            <RadioGroupItem value="resume_only" id="scope-resume" />
            <Label
              htmlFor="scope-resume"
              className="font-normal cursor-pointer"
            >
              This resume only
            </Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem value="global" id="scope-global" />
            <Label
              htmlFor="scope-global"
              className="font-normal cursor-pointer"
            >
              All resumes &amp; portfolio
            </Label>
          </div>
        </RadioGroup>
      </div>

      <Separator />

      <div className="flex items-center gap-2">
        <Button onClick={onSave} disabled={saving} className="gap-1.5">
          <Check className="size-4" />
          {saving ? "Saving..." : "Save changes"}
        </Button>
        <Button variant="ghost" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
