import { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import "../Projects.css";
import PublicLayout from "./PublicLayout";
import ProjectCard from "../../components/project-card";
import { publicListProjects, publicFetchThumbnailUrl } from "../../api/public";
import type { Project } from "../../api/projects";

export default function PublicProjectsPage() {
  const { username } = useParams<{ username: string }>();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username) return;
    publicListProjects(username)
      .then(setProjects)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [username]);

  const thumbnailFetcher = useCallback(
    (projectId: number) => publicFetchThumbnailUrl(username!, projectId),
    [username],
  );

  return (
    <PublicLayout>
      <div className="content">
        <h2>Projects</h2>

        {loading && <p>Loading…</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && projects.length === 0 && (
          <p>No projects yet.</p>
        )}

        <div className="projectGrid">
          {projects.map((p) => (
            <ProjectCard
              key={p.project_summary_id}
              projectId={p.project_summary_id}
              name={p.project_name}
              basePath={`/public/${username}/projects`}
              thumbnailFetcher={thumbnailFetcher}
            />
          ))}
        </div>
      </div>
    </PublicLayout>
  );
}
