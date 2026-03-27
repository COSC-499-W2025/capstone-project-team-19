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
import { toShortDate } from "../components/insights/tabs/Skills/utils/formatHelpers";
import {
  AppButton,
  AppField,
  AppInput,
  ConfirmDialog,
  PageContainer,
  PageHeader,
  SectionCard,
  SectionTabs,
  TagPill,
} from "../components/shared";

/** Normalize a date string to YYYY-MM-DD for use in <input type="date">. */
function toDateInputValue(iso?: string | null): string {
  if (!iso) return "";
  const match = iso.match(/^\d{4}-\d{2}-\d{2}/);
  return match ? match[0] : "";
}

function normalizeContributionSummary(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const text = value.trim();
  if (!text) return null;
  if (/^\[no .*provided\]$/i.test(text)) return null;
  if (/^\[no .*available\]$/i.test(text)) return null;
  return text;
}

function resolveContributionSummary(project: ProjectDetail): string | null {
  const contributions = project.contributions ?? {};
  const textCollab =
    contributions.text_collab && typeof contributions.text_collab === "object"
      ? contributions.text_collab
      : null;

  const candidates: unknown[] = [
    contributions.llm_contribution_summary,
    textCollab?.contribution_summary,
    contributions.manual_contribution_summary,
    contributions.non_llm_contribution_summary,
  ];

  for (const candidate of candidates) {
    const normalized = normalizeContributionSummary(candidate);
    if (normalized) return normalized;
  }
  return null;
}

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
        setStartDate(toDateInputValue(dateItem?.start_date));
        setEndDate(toDateInputValue(dateItem?.end_date));
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
      setStartDate(toDateInputValue(updated.start_date));
      setEndDate(toDateInputValue(updated.end_date));
      setEditingDates(false);
    } catch (e: unknown) {
      setDatesError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSavingDates(false);
    }
  }

  function handleCancelDates() {
    setStartDate(toDateInputValue(dates?.start_date));
    setEndDate(toDateInputValue(dates?.end_date));
    setDatesError(null);
    setEditingDates(false);
  }

  async function handleResetDates() {
    setSavingDates(true);
    setDatesError(null);
    try {
      const updated = await resetProjectDates(projectId);
      setDates(updated);
      setStartDate(toDateInputValue(updated.start_date));
      setEndDate(toDateInputValue(updated.end_date));
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
  const contributionSummaryText = resolveContributionSummary(project);

  return (
    <>
      <TopBar showNav username={username} />

      <PageContainer className="flex min-h-[calc(100vh-56px)] flex-col gap-[20px] bg-background pt-[12px]">
        <PageHeader
          title={project.project_name}
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "Projects", href: "/projects" },
            { label: project.project_name },
          ]}
          actions={
            <AppButton variant="destructive" onClick={() => setConfirmDelete(true)}>
              Delete Project
            </AppButton>
          }
        />

        {/* Thumbnail + Meta */}
        <SectionCard className="w-full bg-white">
          <div className="flex gap-[20px]">
            <div className="shrink-0 space-y-[8px]">
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
              <div className="flex gap-[6px]">
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

            <div className="flex flex-wrap gap-[8px] self-start">
              {project.project_type && (
                <TagPill className="capitalize">{project.project_type}</TagPill>
              )}
              {project.project_mode && (
                <TagPill className="capitalize">{project.project_mode}</TagPill>
              )}
            </div>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleThumbnailChange}
          />
        </SectionCard>

        {/* Duration — light panel; view: title + range left, Edit top-right; edit: stacked fields + full-width primary actions */}
        <SectionCard className="w-full rounded-[10px] border-[#e0e0e0] bg-[#f4f4f6] px-[22px] py-[20px]">
          {!editingDates ? (
            <div className="flex items-start justify-between gap-[16px]">
              <div className="min-w-0 flex-1 space-y-[10px]">
                <div className="text-[18px] font-medium leading-none text-foreground">
                  Duration
                </div>
                <div className="flex flex-wrap items-center gap-[8px]">
                  <span className="text-[14px] leading-[1.5] text-[#4a4a4a]">
                    {!dates?.start_date && !dates?.end_date
                      ? "No dates available"
                      : !dates?.start_date
                        ? `Unknown start – ${toShortDate(dates?.end_date)}`
                        : !dates?.end_date
                          ? `${toShortDate(dates?.start_date)} – Present`
                          : `${toShortDate(dates?.start_date)} – ${toShortDate(dates?.end_date)}`}
                  </span>
                  {dates?.source === "MANUAL" && (
                    <TagPill className="text-[12px]">manual</TagPill>
                  )}
                </div>
              </div>
              <AppButton
                variant="outline"
                size="sm"
                className="shrink-0"
                onClick={() => {
                  setStartDate(toDateInputValue(dates?.start_date));
                  setEndDate(toDateInputValue(dates?.end_date));
                  setEditingDates(true);
                }}
              >
                Edit
              </AppButton>
            </div>
          ) : (
            <div className="space-y-[18px]">
              <div className="text-[18px] font-medium leading-none text-foreground">
                Duration
              </div>
              {/* Narrow column — matches compact date + action layout */}
              <div className="w-full max-w-[248px] space-y-[16px]">
                <div className="flex flex-col gap-[16px]">
                  <AppField label="Start date">
                    <AppInput
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                    className="h-[40px] w-full rounded-[8px] border-[#cfd5df] bg-white"
                  />
                </AppField>
                <AppField label="End date">
                  <AppInput
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="h-[40px] w-full rounded-[8px] border-[#cfd5df] bg-white"
                    />
                  </AppField>
                </div>
                {datesError && (
                  <p className="text-[13px] leading-[1.3] text-[#cc4b4b]">{datesError}</p>
                )}
                <div className="flex max-w-[248px] gap-[10px]">
                  <AppButton
                    type="button"
                    variant="primary"
                    className="h-[40px] min-h-0 flex-1 rounded-[8px] px-[12px] text-[14px] font-medium"
                    onClick={handleSaveDates}
                    disabled={savingDates}
                  >
                    {savingDates ? "Saving…" : "Save"}
                  </AppButton>
                  <AppButton
                    type="button"
                    variant="primary"
                    className="h-[40px] min-h-0 flex-1 rounded-[8px] px-[12px] text-[14px] font-medium"
                    onClick={handleCancelDates}
                    disabled={savingDates}
                  >
                    Cancel
                  </AppButton>
                </div>
                {dates?.source === "MANUAL" && (
                  <div className="max-w-[248px] pt-[2px]">
                    <AppButton
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="w-full text-[13px] text-primary"
                      onClick={handleResetDates}
                      disabled={savingDates}
                    >
                      Reset to auto
                    </AppButton>
                  </div>
                )}
              </div>
            </div>
          )}
        </SectionCard>

        {/* Summary / Feedback */}
        <SectionCard className="w-full space-y-[16px] bg-white">
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
                    {contributionSummaryText ?? (
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
