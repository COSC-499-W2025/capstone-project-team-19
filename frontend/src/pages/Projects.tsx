import { useEffect, useState } from "react";
import TopBar from "../components/TopBar";
import ProjectCard from "../components/project-card";
import { listProjects, type Project } from "../api/projects";
import { getUsername } from "../auth/user";

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
      <div className="content">
        <h2>Projects</h2>

        {loading && <p>Loading…</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && projects.length === 0 && (
          <p>No projects yet. Upload one to get started.</p>
        )}

        <div className="projectGrid">
          {projects.map((p) => (
            <ProjectCard
              key={p.project_summary_id}
              projectId={p.project_summary_id}
              name={p.project_name}
            />
          ))}
        </div>
      </div>
    </>
  );
}