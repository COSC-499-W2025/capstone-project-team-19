import { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import "./Projects.css";
import TopBar from "../components/TopBar";
import { fetchThumbnailUrl, listProjects, type Project } from "../api/projects";
import { getUsername } from "../auth/user";
import {
  FeatureTile,
  PageContainer,
  PageHeader,
  SectionCard,
  TagPill,
} from "../components/shared";

export default function ProjectsPage() {
  const username = getUsername();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [thumbnails, setThumbnails] = useState<Record<number, string | null>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState<number | null>(null);
  const [autoOpenAttempted, setAutoOpenAttempted] = useState(false);

  const requestedProjectName = (searchParams.get("openProject") ?? "").trim();
  const openedFromUpload = searchParams.get("openedFromUpload") === "1";
  const returnTo = (searchParams.get("returnTo") ?? "").trim();

  useEffect(() => {
    let cancelled = false;
    const objectUrls: string[] = [];

    listProjects()
      .then((list) => {
        if (cancelled) return;
        setProjects(list);
        Promise.all(
          list.map((p) =>
            fetchThumbnailUrl(p.project_summary_id).then((url) => ({
              id: p.project_summary_id,
              url,
            })),
          ),
        ).then((results) => {
          if (cancelled) return;
          const map: Record<number, string | null> = {};
          for (const { id, url } of results) {
            map[id] = url;
            if (url) objectUrls.push(url);
          }
          setThumbnails(map);
        });
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      for (const url of objectUrls) URL.revokeObjectURL(url);
    };
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

      <PageContainer className="flex min-h-[calc(100vh-56px)] flex-col gap-[20px] bg-background pt-[12px]">
        <PageHeader
          title="Projects"
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "Projects" },
          ]}
        />

        {loading && (
          <SectionCard className="w-full bg-white">
            <p className="text-[14px] text-[#7f7f7f]">Loading…</p>
          </SectionCard>
        )}

        {error && (
          <SectionCard className="w-full bg-white">
            <p className="text-[14px] text-[#cc4b4b]">{error}</p>
          </SectionCard>
        )}

        {!loading && !error && projects.length === 0 && (
          <SectionCard className="w-full bg-white">
            <p className="text-[14px] text-[#7f7f7f]">
              No projects yet. Upload one to get started.
            </p>
          </SectionCard>
        )}

        {!loading && !error && projects.length > 0 && (
          <SectionCard className="w-full bg-white">
            <div className="flex flex-wrap gap-[20px]">
              {projects.map((p) => (
                <div key={p.project_summary_id} className="relative">
                  <FeatureTile
                    title={p.project_name}
                    thumbnailUrl={thumbnails[p.project_summary_id]}
                    onClick={() => nav(`/projects/${p.project_summary_id}`)}
                  />
                  <TagPill
                    className={`pointer-events-none absolute right-[8px] top-[8px] z-10 px-[8px] py-[2px] text-[11px] font-medium ${
                      p.is_public
                        ? "border-sky-300 bg-sky-100/95 text-sky-900"
                        : "border-[#d0d0d0] bg-white/[0.92] text-[#6b6b6b]"
                    }`}
                    aria-label={
                      p.is_public
                        ? "This project is visible on your public portfolio"
                        : "This project is private"
                    }
                  >
                    {p.is_public ? "Public" : "Private"}
                  </TagPill>
                </div>
              ))}
            </div>
          </SectionCard>
        )}
      </PageContainer>
    </>
  );
}
