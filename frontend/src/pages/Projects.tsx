import { useEffect, useState } from "react";
import "./Projects.css";
import TopBar from "../components/TopBar";
import ProjectCard from "../components/project-card";
import { listProjects, type Project } from "../api/projects";
import { getUsername } from "../auth/user";
import { PageContainer, PageHeader, SectionCard } from "../components/shared";

export default function ProjectsPage() {
  const username = getUsername();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProjects()
      .then(setProjects)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

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
                    <span
                      className={`projectVisibilityTag${
                        p.is_public ? " public" : ""
                      }`}
                      title={
                        p.is_public
                          ? "Visible on public dashboard"
                          : "Hidden from public dashboard"
                      }
                    >
                      {p.is_public ? "Public" : "Private"}
                    </span>
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