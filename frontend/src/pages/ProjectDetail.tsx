import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./ProjectDetail.css";
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
import { PageContainer, PageHeader, SectionCard } from "../components/shared";

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
      const updated = await patchProjectDates(
        projectId,
        startDate || null,
        endDate || null,
      );
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
        <div className="min-h-[calc(100vh-56px)] bg-background">
          <PageContainer className="pt-[12px]">
            <PageHeader
              title="Project Detail"
              breadcrumbs={[
                { label: "Home", href: "/" },
                { label: "Projects", href: "/projects" },
                { label: "Project Detail" },
              ]}
            />
            <SectionCard className="w-full max-w-[1110px] self-center bg-white">
              <div className="content">
                <p>Loading…</p>
              </div>
            </SectionCard>
          </PageContainer>
        </div>
      </>
    );
  }

  if (error || !project) {
    return (
      <>
        <TopBar showNav username={username} />
        <div className="min-h-[calc(100vh-56px)] bg-background">
          <PageContainer className="pt-[12px]">
            <PageHeader
              title="Project Detail"
              breadcrumbs={[
                { label: "Home", href: "/" },
                { label: "Projects", href: "/projects" },
                { label: "Project Detail" },
              ]}
            />
            <SectionCard className="w-full max-w-[1110px] self-center bg-white">
              <div className="content">
                <p className="error">{error ?? "Project not found."}</p>
                <button className="btn" onClick={() => nav("/projects")}>
                  ← Back to Projects
                </button>
              </div>
            </SectionCard>
          </PageContainer>
        </div>
      </>
    );
  }

  const currentIndex = allProjects.findIndex(
    (p) => p.project_summary_id === projectId
  );
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
    {}
  );

  return (
    <>
      {confirmRemoveThumbnail && (
        <div className="pdModalOverlay">
          <div className="pdModal">
            <p>Remove this thumbnail? This cannot be undone.</p>
            <div className="pdFormActions">
              <button
                className="btn pdThumbBtnDanger"
                onClick={() => {
                  setConfirmRemoveThumbnail(false);
                  handleRemoveThumbnail();
                }}
                disabled={thumbLoading}
              >
                {thumbLoading ? "Removing…" : "Yes, remove"}
              </button>
              <button
                className="btn"
                onClick={() => setConfirmRemoveThumbnail(false)}
                disabled={thumbLoading}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <TopBar showNav username={username} />

      <div className="min-h-[calc(100vh-56px)] bg-background">
        <PageContainer className="pt-[12px]">
          <PageHeader
            title={project.project_name}
            breadcrumbs={[
              { label: "Home", href: "/" },
              { label: "Projects", href: "/projects" },
              { label: project.project_name },
            ]}
          />

          <SectionCard className="w-full max-w-[1110px] self-center bg-white">
            <div className="content">
              <button className="pdBackBtn" onClick={() => nav("/projects")}>
                ← Back to Projects
              </button>

              {/* Header */}
              <div className="pdHeader">
                {/* Thumbnail */}
                <div className="pdThumbWrap">
                  <div
                    className="pdThumb"
                    style={thumbUrl ? { backgroundImage: `url(${thumbUrl})` } : undefined}
                  >
                    {!thumbUrl && <span className="pdThumbPlaceholder">No Image</span>}
                    {thumbLoading && <div className="pdThumbOverlay">Uploading…</div>}
                  </div>
                  <div className="pdThumbActions">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      style={{ display: "none" }}
                      onChange={handleThumbnailChange}
                    />
                    <button
                      className="btn pdThumbBtn"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={thumbLoading}
                    >
                      {thumbUrl ? "Change" : "Upload"} Thumbnail
                    </button>
                    {thumbUrl && (
                      <button
                        className="btn pdThumbBtnDanger"
                        onClick={() => setConfirmRemoveThumbnail(true)}
                        disabled={thumbLoading}
                      >
                        Remove Thumbnail
                      </button>
                    )}
                  </div>
                  {thumbError && <p className="error">{thumbError}</p>}
                </div>

                {/* Project name + meta */}
                <div className="pdHeaderInfo">
                  <h2 className="pdTitle">{project.project_name}</h2>
                  {project.project_type && (
                    <span className="pdMeta">{project.project_type}</span>
                  )}
                  {project.project_mode && (
                    <span className="pdMeta">{project.project_mode}</span>
                  )}
                </div>

                {!confirmDelete ? (
                  <button
                    className="primaryBtn pdDeleteBtn"
                    onClick={() => setConfirmDelete(true)}
                  >
                    Delete Project
                  </button>
                ) : (
                  <div className="pdDeleteConfirm">
                    <p>Are you sure? This cannot be undone.</p>
                    <div className="pdFormActions">
                      <button
                        className="primaryBtn pdDeleteBtn"
                        onClick={handleDeleteProject}
                        disabled={deleting}
                      >
                        {deleting ? "Deleting…" : "Yes, delete"}
                      </button>
                      <button
                        className="btn"
                        onClick={() => setConfirmDelete(false)}
                        disabled={deleting}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Duration */}
              <div className="pdSection">
                <div className="pdSectionHeader">
                  <h3>Duration</h3>
                  {!editingDates && (
                    <button
                      className="pdEditBtn"
                      onClick={() => setEditingDates(true)}
                    >
                      Edit
                    </button>
                  )}
                </div>
                {!editingDates ? (
                  <p className="pdDateDisplay">
                    {formatDate(dates?.start_date)} → {formatDate(dates?.end_date)}
                    {dates?.source === "MANUAL" && (
                      <span className="pdDateTag">manual</span>
                    )}
                  </p>
                ) : (
                  <div className="pdDateForm">
                    <label>
                      Start date
                      <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                      />
                    </label>
                    <label>
                      End date
                      <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                      />
                    </label>
                    {datesError && <p className="error">{datesError}</p>}
                    <div className="pdFormActions">
                      <button
                        className="primaryBtn"
                        onClick={handleSaveDates}
                        disabled={savingDates}
                      >
                        {savingDates ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn"
                        onClick={handleCancelDates}
                        disabled={savingDates}
                      >
                        Cancel
                      </button>
                      {dates?.source === "MANUAL" && (
                        <button
                          className="btn"
                          onClick={handleResetDates}
                          disabled={savingDates}
                        >
                          Reset to auto
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Summary */}
              <div className="pdSection">
                <h3>Summary</h3>
                <p className="pdSummaryText">
                  {project.summary_text ?? <em>No summary yet.</em>}
                </p>
                {project.project_mode === "collaborative" && (
                  <>
                    <h3 className="pdContribHeading">Contribution Summary</h3>
                    <p className="pdSummaryText">
                      {project.contributions?.manual_contribution_summary ?? (
                        <em>No contribution summary yet.</em>
                      )}
                    </p>
                  </>
                )}
              </div>

              {/* Feedback */}
              <div className="pdSection">
                <h3>Feedback</h3>
                {feedback.length === 0 ? (
                  <p className="pdEmpty">No feedback available for this project.</p>
                ) : (
                  Object.entries(feedbackBySkill).map(([skill, items]) => (
                    <div key={skill} className="pdFeedbackGroup">
                      <h4 className="pdFeedbackSkill">{formatSkillName(skill)}</h4>
                      {items.map((item, i) => (
                        <div
                          key={item.feedback_id ?? i}
                          className="pdFeedbackItem"
                        >
                          {item.suggestion && (
                            <p className="pdFeedbackSuggestion">
                              {item.suggestion}
                            </p>
                          )}
                          {item.file_name && (
                            <span className="pdFeedbackFile">
                              {item.file_name}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  ))
                )}
              </div>

              {/* Prev/Next navigation */}
              {(prevProject || nextProject) && (
                <div className="pdNavRow">
                  {prevProject ? (
                    <button
                      className="pdNavBtn"
                      onClick={() =>
                        nav(`/projects/${prevProject.project_summary_id}`)
                      }
                    >
                      ← {prevProject.project_name}
                    </button>
                  ) : (
                    <span />
                  )}
                  {nextProject && (
                    <button
                      className="pdNavBtn"
                      onClick={() =>
                        nav(`/projects/${nextProject.project_summary_id}`)
                      }
                    >
                      {nextProject.project_name} →
                    </button>
                  )}
                </div>
              )}
            </div>
          </SectionCard>
        </PageContainer>
      </div>
    </>
  );
}