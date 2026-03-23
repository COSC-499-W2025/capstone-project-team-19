import { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import "./Projects.css";
import TopBar from "../components/TopBar";
import ProjectCard from "../components/project-card";
import { listProjects, type Project } from "../api/projects";
import { updateProjectVisibility } from "../api/portfolioSettings";
import { getUsername } from "../auth/user";
import { PageContainer, PageHeader, SectionCard } from "../components/shared";

export default function ProjectsPage() {
  const username = getUsername();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState<number | null>(null);
  const [autoOpenAttempted, setAutoOpenAttempted] = useState(false);

  const requestedProjectName = (searchParams.get("openProject") ?? "").trim();
  const openedFromUpload = searchParams.get("openedFromUpload") === "1";
  const returnTo = (searchParams.get("returnTo") ?? "").trim();

  useEffect(() => {
    listProjects()
      .then(setProjects)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (autoOpenAttempted) return;
    if (!requestedProjectName) {
      setAutoOpenAttempted(true);
      return;
    }
    if (loading) return;

    setAutoOpenAttempted(true);
    const target = projects.find(
      (project) => project.project_name.trim().toLowerCase() === requestedProjectName.toLowerCase(),
    );
    if (!target) return;

    const detailQuery = new URLSearchParams();
    if (openedFromUpload) detailQuery.set("openedFromUpload", "1");
    if (returnTo) detailQuery.set("returnTo", returnTo);

    const suffix = detailQuery.toString();
    nav(`/projects/${target.project_summary_id}${suffix ? `?${suffix}` : ""}`, { replace: true });
  }, [autoOpenAttempted, loading, nav, openedFromUpload, projects, requestedProjectName, returnTo]);

  const handleToggleVisibility = useCallback(
    async (e: React.MouseEvent, project: Project) => {
      e.stopPropagation();
      if (toggling === project.project_summary_id) return;
      setToggling(project.project_summary_id);
      const newValue = !project.is_public;

      try {
        await updateProjectVisibility(project.project_summary_id, newValue);
        setProjects((prev) =>
          prev.map((p) =>
            p.project_summary_id === project.project_summary_id
              ? { ...p, is_public: newValue }
              : p
          )
        );
      } catch {
        // state stays unchanged on error
      } finally {
        setToggling(null);
      }
    },
    [toggling]
  );

  return (
    <>
      <TopBar showNav username={username} />

      <div className="min-h-[calc(100vh-56px)] bg-background">
        <PageContainer className="pt-[12px]">
          <PageHeader
            title="Projects"
            breadcrumbs={[
              { label: "Home", href: "/" },
              { label: "Projects" },
            ]}
          />

          <SectionCard className="w-full max-w-[1110px] self-center bg-white">
            <div className="content">

              {loading && <p>Loading…</p>}
              {error && <p className="error">{error}</p>}

              {!loading && !error && projects.length === 0 && (
                <p>No projects yet. Upload one to get started.</p>
              )}

              <div className="projectGrid">
                {projects.map((p) => (
                  <div key={p.project_summary_id} className="projectCardWrapper">
                    <ProjectCard
                      projectId={p.project_summary_id}
                      name={p.project_name}
                    />
                    <button
                      className={`projectVisibilityToggle${
                        p.is_public ? " public" : ""
                      }`}
                      onClick={(e) => handleToggleVisibility(e, p)}
                      disabled={toggling === p.project_summary_id}
                      title={
                        p.is_public
                          ? "Visible on public portfolio — click to hide"
                          : "Hidden from public portfolio — click to show"
                      }
                    >
                      {toggling === p.project_summary_id
                        ? "…"
                        : p.is_public
                        ? "Public"
                        : "Private"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </SectionCard>
        </PageContainer>
      </div>
    </>
  );
}
