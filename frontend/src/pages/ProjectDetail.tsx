import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";
import {
  deleteProject,
  deleteThumbnail,
  fetchThumbnailUrl,
  getProject,
  getProjectDates,
  getProjectFeedback,
  listProjects,
  patchProjectDates,
  resetProjectDates,
  uploadThumbnail,
  type FeedbackItem,
  type Project,
  type ProjectDatesItem,
  type ProjectDetail,
} from "../api/projects";
import { updateProjectVisibility } from "../api/portfolioSettings";
import {
  AppButton,
  AppField,
  AppInput,
  Breadcrumbs,
  ConfirmDialog,
  PageContainer,
  PageHeader,
  SectionCard,
  SectionTabs,
  TagPill,
} from "../components/shared";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const nav = useNavigate();
  const username = getUsername();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [thumbUrl, setThumbUrl] = useState<string | null>(null);
  const [dates, setDates] = useState<ProjectDatesItem | null>(null);
  const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
  const [allProjects, setAllProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dates editing
  const [editingDates, setEditingDates] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [savingDates, setSavingDates] = useState(false);
  const [datesError, setDatesError] = useState<string | null>(null);

  // Thumbnail
  const [thumbLoading, setThumbLoading] = useState(false);
  const [thumbError, setThumbError] = useState<string | null>(null);
  const [confirmRemoveThumbnail, setConfirmRemoveThumbnail] = useState(false);

  // Delete
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  // Visibility (public dashboard)
  const [savingVisibility, setSavingVisibility] = useState(false);

  // Tabs
  const [activeTab, setActiveTab] = useState("summary");

  useEffect(() => {
    let objectUrl: string | null = null;
    Promise.all([
      getProject(projectId),
      fetchThumbnailUrl(projectId),
      getProjectDates(projectId),
      getProjectFeedback(projectId),
      listProjects(),
    ])
      .then(([proj, thumb, dateItem, fb, projects]) => {
        setProject(proj);
        objectUrl = thumb;
        setThumbUrl(thumb);
        setDates(dateItem);
        setFeedback(fb);
        setAllProjects(projects);
        setStartDate(dateItem?.start_date ?? "");
        setEndDate(dateItem?.end_date ?? "");
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [projectId]);

  async function handleThumbnailChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setThumbLoading(true);
    setThumbError(null);
    try {
      await uploadThumbnail(projectId, file);
      const newUrl = await fetchThumbnailUrl(projectId);
      if (thumbUrl) URL.revokeObjectURL(thumbUrl);
      setThumbUrl(newUrl);
    } catch (e: unknown) {
      setThumbError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setThumbLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleRemoveThumbnail() {
    setThumbLoading(true);
    setThumbError(null);
    try {
      await deleteThumbnail(projectId);
      if (thumbUrl) URL.revokeObjectURL(thumbUrl);
      setThumbUrl(null);
    } catch (e: unknown) {
      setThumbError(e instanceof Error ? e.message : "Remove failed");
    } finally {
      setThumbLoading(false);
    }
  }

  async function handleSaveDates() {
    setSavingDates(true);
    setDatesError(null);
    try {
      const updated = await patchProjectDates(projectId, startDate || null, endDate || null);
      setDates(updated);
      setStartDate(updated.start_date ?? "");
      setEndDate(updated.end_date ?? "");
      setEditingDates(false);
    } catch (e: unknown) {
      setDatesError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSavingDates(false);
    }
  }

  function handleCancelDates() {
    setStartDate(dates?.start_date ?? "");
    setEndDate(dates?.end_date ?? "");
    setDatesError(null);
    setEditingDates(false);
  }

  async function handleResetDates() {
    setSavingDates(true);
    setDatesError(null);
    try {
      const updated = await resetProjectDates(projectId);
      setDates(updated);
      setStartDate(updated.start_date ?? "");
      setEndDate(updated.end_date ?? "");
      setEditingDates(false);
    } catch (e: unknown) {
      setDatesError(e instanceof Error ? e.message : "Reset failed");
    } finally {
      setSavingDates(false);
    }
  }

  async function handleDeleteProject() {
    setDeleting(true);
    try {
      await deleteProject(projectId);
      nav("/projects");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed");
      setDeleting(false);
      setConfirmDelete(false);
    }
  }

  const isPublic =
    allProjects.find((p) => p.project_summary_id === projectId)?.is_public ?? false;

  async function handleVisibilityChange(newIsPublic: boolean) {
    if (newIsPublic === isPublic || savingVisibility) return;
    setSavingVisibility(true);
    try {
      await updateProjectVisibility(projectId, newIsPublic);
      setAllProjects((prev) =>
        prev.map((p) =>
          p.project_summary_id === projectId ? { ...p, is_public: newIsPublic } : p,
        ),
      );
    } catch {
      // state stays unchanged on error
    } finally {
      setSavingVisibility(false);
    }
  }

  function formatDate(d: string | null | undefined) {
    if (!d) return "—";
    return d;
  }

  function formatSkillName(s: string) {
    return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  if (loading) {
    return (
      <>
        <TopBar showNav username={username} />
        <PageContainer className="min-h-[calc(100vh-56px)] bg-background pt-[12px]">
          <PageHeader
            title="Project Detail"
            breadcrumbs={[
              { label: "Home", href: "/" },
              { label: "Projects", href: "/projects" },
              { label: "Project Detail" },
            ]}
          />
          <SectionCard className="w-full bg-white">
            <p className="text-[14px] text-[#7f7f7f]">Loading…</p>
          </SectionCard>
        </PageContainer>
      </>
    );
  }

  if (error || !project) {
    return (
      <>
        <TopBar showNav username={username} />
        <PageContainer className="flex min-h-[calc(100vh-56px)] flex-col gap-[20px] bg-background pt-[12px]">
          <PageHeader
            title="Project Detail"
            breadcrumbs={[
              { label: "Home", href: "/" },
              { label: "Projects", href: "/projects" },
              { label: "Project Detail" },
            ]}
          />
          <SectionCard className="w-full bg-white">
            <p className="text-[14px] text-[#cc4b4b]">{error ?? "Project not found."}</p>
            <div className="mt-[12px]">
              <AppButton variant="ghost" onClick={() => nav("/projects")}>
                ← Back to Projects
              </AppButton>
            </div>
          </SectionCard>
        </PageContainer>
      </>
    );
  }

  const currentIndex = allProjects.findIndex((p) => p.project_summary_id === projectId);
  const prevProject = currentIndex > 0 ? allProjects[currentIndex - 1] : null;
  const nextProject =
    currentIndex !== -1 && currentIndex < allProjects.length - 1
      ? allProjects[currentIndex + 1]
      : null;

  const feedbackBySkill = feedback.reduce<Record<string, FeedbackItem[]>>(
    (acc, item) => {
      if (!acc[item.skill_name]) acc[item.skill_name] = [];
      acc[item.skill_name].push(item);
      return acc;
    },
    {},
  );

  return (
    <>
      <TopBar showNav username={username} />

      <PageContainer className="flex min-h-[calc(100vh-56px)] flex-col gap-8 bg-background pt-[12px]">
        <header className="flex flex-col gap-2 pt-[10px] pb-[6px]">
          <Breadcrumbs
            items={[
              { label: "Home", href: "/" },
              { label: "Projects", href: "/projects" },
              { label: project.project_name },
            ]}
          />
          <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
            <h1 className="text-[20px] font-medium leading-none text-foreground">
              {project.project_name}
            </h1>
            {project.project_type && (
              <TagPill className="capitalize">{project.project_type}</TagPill>
            )}
            {project.project_mode && (
              <TagPill className="capitalize">{project.project_mode}</TagPill>
            )}
          </div>
          <div className="mt-5 w-full">
            <AppButton variant="destructive" onClick={() => setConfirmDelete(true)}>
              Delete Project
            </AppButton>
          </div>
        </header>

        {/* Thumbnail */}
        <SectionCard className="w-full bg-white px-6 py-6">
          <div className="shrink-0 space-y-2">
            <div
              className="relative h-[140px] w-[186px] overflow-hidden rounded-[6px] bg-[#ebebeb] bg-cover bg-center"
              style={thumbUrl ? { backgroundImage: `url(${thumbUrl})` } : undefined}
            >
              {!thumbUrl && (
                <div className="flex h-full items-center justify-center text-[13px] text-[#9f9f9f]">
                  No Image
                </div>
              )}
              {thumbLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/30 text-[13px] text-white">
                  Uploading…
                </div>
              )}
            </div>
            <div className="flex gap-[6px] pt-1">
              <AppButton
                variant="outline"
                size="sm"
                disabled={thumbLoading}
                onClick={() => fileInputRef.current?.click()}
              >
                {thumbUrl ? "Change" : "Upload"} Thumbnail
              </AppButton>
              {thumbUrl && (
                <AppButton
                  variant="destructive"
                  size="sm"
                  disabled={thumbLoading}
                  onClick={() => setConfirmRemoveThumbnail(true)}
                >
                  Remove Thumbnail
                </AppButton>
              )}
            </div>
            {thumbError && <p className="text-[13px] text-[#cc4b4b]">{thumbError}</p>}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleThumbnailChange}
          />
        </SectionCard>

        {/* Public dashboard visibility */}
        <SectionCard className="w-full bg-white px-6 py-6">
          <div className="flex flex-col gap-2">
            <div className="text-[18px] font-medium leading-snug text-foreground">
              Public dashboard visibility
            </div>
            <p className="m-0 max-w-[640px] text-[13px] leading-[1.5] text-[#555]">
              This controls whether this project is shown on your public dashboard. Private projects
              are only visible to you.
            </p>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <div
              className="inline-flex overflow-hidden rounded-md border border-slate-300 bg-white shadow-sm"
              role="group"
              aria-label="Project visibility"
            >
              <button
                type="button"
                className={`border-0 border-r border-slate-300 px-4 py-2 text-[13px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-70 ${
                  !isPublic
                    ? "bg-[#001166] text-white hover:bg-[#001f8c]"
                    : "cursor-pointer bg-white text-slate-600 hover:bg-sky-50 hover:text-[#1a5fa8]"
                }`}
                onClick={() => handleVisibilityChange(false)}
                disabled={savingVisibility}
                aria-pressed={!isPublic}
              >
                Private
              </button>
              <button
                type="button"
                className={`border-0 px-4 py-2 text-[13px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-70 ${
                  isPublic
                    ? "bg-[#001166] text-white hover:bg-[#001f8c]"
                    : "cursor-pointer bg-white text-slate-600 hover:bg-sky-50 hover:text-[#1a5fa8]"
                }`}
                onClick={() => handleVisibilityChange(true)}
                disabled={savingVisibility}
                aria-pressed={isPublic}
              >
                Public
              </button>
            </div>
            {savingVisibility && (
              <span className="text-[12px] italic text-[#6b7280]">Saving…</span>
            )}
          </div>
        </SectionCard>

        {/* Duration */}
        <SectionCard className="w-full space-y-4 bg-white px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="text-[18px] font-medium leading-none text-foreground">Duration</div>
            {!editingDates && (
              <AppButton variant="outline" size="sm" onClick={() => setEditingDates(true)}>
                Edit
              </AppButton>
            )}
          </div>

          {!editingDates ? (
            <div className="flex items-center gap-[8px]">
              <span className="text-[14px] text-foreground">
                {formatDate(dates?.start_date)} → {formatDate(dates?.end_date)}
              </span>
              {dates?.source === "MANUAL" && (
                <TagPill className="text-[12px]">manual</TagPill>
              )}
            </div>
          ) : (
            <div className="space-y-[14px]">
              <div className="grid gap-[14px] md:grid-cols-2">
                <AppField label="Start date">
                  <AppInput
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </AppField>
                <AppField label="End date">
                  <AppInput
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </AppField>
              </div>
              {datesError && <p className="text-[13px] text-[#cc4b4b]">{datesError}</p>}
              <div className="flex gap-[8px]">
                <AppButton onClick={handleSaveDates} disabled={savingDates}>
                  {savingDates ? "Saving…" : "Save"}
                </AppButton>
                <AppButton variant="outline" onClick={handleCancelDates} disabled={savingDates}>
                  Cancel
                </AppButton>
                {dates?.source === "MANUAL" && (
                  <AppButton variant="ghost" onClick={handleResetDates} disabled={savingDates}>
                    Reset to auto
                  </AppButton>
                )}
              </div>
            </div>
          )}
        </SectionCard>

        {/* Summary / Feedback */}
        <SectionCard className="w-full space-y-4 bg-white px-6 py-6">
          <SectionTabs
            tabs={[
              { key: "summary", label: "Summary" },
              { key: "feedback", label: "Feedback" },
            ]}
            activeKey={activeTab}
            onChange={setActiveTab}
            align="left"
          />

          {activeTab === "summary" && (
            <div className="space-y-[14px]">
              <p className="whitespace-pre-wrap text-[14px] leading-[1.6] text-foreground">
                {project.summary_text ?? <em className="text-[#9f9f9f]">No summary yet.</em>}
              </p>
              {project.project_mode === "collaborative" && (
                <>
                  <div className="text-[16px] font-medium text-foreground">
                    Contribution Summary
                  </div>
                  <p className="whitespace-pre-wrap text-[14px] leading-[1.6] text-foreground">
                    {project.contributions?.manual_contribution_summary ?? (
                      <em className="text-[#9f9f9f]">No contribution summary yet.</em>
                    )}
                  </p>
                </>
              )}
            </div>
          )}

          {activeTab === "feedback" && (
            <div className="space-y-[20px]">
              {feedback.length === 0 ? (
                <p className="text-[14px] text-[#7f7f7f]">
                  No feedback available for this project.
                </p>
              ) : (
                Object.entries(feedbackBySkill).map(([skill, items]) => (
                  <div key={skill} className="space-y-[8px]">
                    <div className="text-[14px] font-medium text-foreground">
                      {formatSkillName(skill)}
                    </div>
                    {items.map((item, i) => (
                      <div
                        key={item.feedback_id ?? i}
                        className="rounded-[4px] border border-[#e0e0e0] bg-white px-[12px] py-[10px]"
                      >
                        {item.suggestion && (
                          <p className="text-[14px] leading-[1.5] text-foreground">
                            {item.suggestion}
                          </p>
                        )}
                        {item.file_name && (
                          <span className="mt-[4px] block text-[12px] italic text-[#7f7f7f]">
                            {item.file_name}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                ))
              )}
            </div>
          )}
        </SectionCard>

        {/* Prev/Next navigation */}
        {(prevProject || nextProject) && (
          <div className="flex justify-between">
            {prevProject ? (
              <AppButton
                variant="ghost"
                onClick={() => nav(`/projects/${prevProject.project_summary_id}`)}
              >
                ← {prevProject.project_name}
              </AppButton>
            ) : (
              <span />
            )}
            {nextProject && (
              <AppButton
                variant="ghost"
                onClick={() => nav(`/projects/${nextProject.project_summary_id}`)}
              >
                {nextProject.project_name} →
              </AppButton>
            )}
          </div>
        )}
      </PageContainer>

      <ConfirmDialog
        open={confirmRemoveThumbnail}
        onOpenChange={setConfirmRemoveThumbnail}
        title="Remove Thumbnail"
        description="Remove this thumbnail? This cannot be undone."
        confirmLabel="Remove"
        onConfirm={handleRemoveThumbnail}
      />

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={(open) => { if (!deleting) setConfirmDelete(open); }}
        title="Delete Project"
        description="Are you sure you want to delete this project? This cannot be undone."
        confirmLabel="Delete"
        onConfirm={handleDeleteProject}
      />
    </>
  );
}