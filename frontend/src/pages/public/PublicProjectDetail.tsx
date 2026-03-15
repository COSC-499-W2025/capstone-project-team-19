import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "../ProjectDetail.css";
import PublicLayout from "./PublicLayout";
import {
  publicGetProject,
  publicFetchThumbnailUrl,
  publicListProjects,
} from "../../api/public";
import type { Project, ProjectDetail } from "../../api/projects";

export default function PublicProjectDetailPage() {
  const { username, id } = useParams<{ username: string; id: string }>();
  const projectId = Number(id);
  const nav = useNavigate();

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [thumbUrl, setThumbUrl] = useState<string | null>(null);
  const [allProjects, setAllProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username) return;
    let objectUrl: string | null = null;

    Promise.all([
      publicGetProject(username, projectId),
      publicFetchThumbnailUrl(username, projectId),
      publicListProjects(username),
    ])
      .then(([proj, thumb, projects]) => {
        setProject(proj);
        objectUrl = thumb;
        setThumbUrl(thumb);
        setAllProjects(projects);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [username, projectId]);

  function formatSkillName(s: string) {
    return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  const basePath = `/public/${username}/projects`;

  if (loading) {
    return (
      <PublicLayout>
        <div className="content"><p>Loading…</p></div>
      </PublicLayout>
    );
  }

  if (error || !project) {
    return (
      <PublicLayout>
        <div className="content">
          <p className="error">{error ?? "Project not found."}</p>
          <button className="btn" onClick={() => nav(basePath)}>← Back to Projects</button>
        </div>
      </PublicLayout>
    );
  }

  const currentIndex = allProjects.findIndex((p) => p.project_summary_id === projectId);
  const prevProject = currentIndex > 0 ? allProjects[currentIndex - 1] : null;
  const nextProject =
    currentIndex !== -1 && currentIndex < allProjects.length - 1
      ? allProjects[currentIndex + 1]
      : null;

  return (
    <PublicLayout>
      <div className="content">
        <button className="pdBackBtn" onClick={() => nav(basePath)}>← Back to Projects</button>

        {/* Header */}
        <div className="pdHeader">
          {/* Thumbnail — read-only */}
          <div className="pdThumbWrap">
            <div
              className="pdThumb"
              style={thumbUrl ? { backgroundImage: `url(${thumbUrl})` } : undefined}
            >
              {!thumbUrl && <span className="pdThumbPlaceholder">No Image</span>}
            </div>
          </div>

          {/* Project name + meta */}
          <div className="pdHeaderInfo">
            <h2 className="pdTitle">{project.project_name}</h2>
            {project.project_type && <span className="pdMeta">{project.project_type}</span>}
            {project.project_mode && <span className="pdMeta">{project.project_mode}</span>}
          </div>
        </div>

        {/* Summary */}
        <div className="pdSection">
          <h3>Summary</h3>
          <p className="pdSummaryText">
            {project.summary_text ?? <em>No summary available.</em>}
          </p>
          {project.project_mode === "collaborative" && (
            <>
              <h3 className="pdContribHeading">Contribution Summary</h3>
              <p className="pdSummaryText">
                {project.contributions?.manual_contribution_summary ?? (
                  <em>No contribution summary available.</em>
                )}
              </p>
            </>
          )}
        </div>

        {/* Skills */}
        {(project.languages?.length > 0 ||
          project.frameworks?.length > 0 ||
          project.skills?.length > 0) && (
          <div className="pdSection">
            <h3>Skills &amp; Technologies</h3>
            {project.languages?.length > 0 && (
              <p className="pdSummaryText">
                <strong>Languages:</strong> {project.languages.join(", ")}
              </p>
            )}
            {project.frameworks?.length > 0 && (
              <p className="pdSummaryText">
                <strong>Frameworks:</strong> {project.frameworks.join(", ")}
              </p>
            )}
            {project.skills?.length > 0 && (
              <p className="pdSummaryText">
                <strong>Skills:</strong>{" "}
                {project.skills.map(formatSkillName).join(", ")}
              </p>
            )}
          </div>
        )}

        {/* Prev/Next navigation */}
        {(prevProject || nextProject) && (
          <div className="pdNavRow">
            {prevProject ? (
              <button
                className="pdNavBtn"
                onClick={() => nav(`${basePath}/${prevProject.project_summary_id}`)}
              >
                ← {prevProject.project_name}
              </button>
            ) : (
              <span />
            )}
            {nextProject && (
              <button
                className="pdNavBtn"
                onClick={() => nav(`${basePath}/${nextProject.project_summary_id}`)}
              >
                {nextProject.project_name} →
              </button>
            )}
          </div>
        )}
      </div>
    </PublicLayout>
  );
}
