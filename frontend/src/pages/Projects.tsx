import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import TopBar from "../components/TopBar";
import { fetchThumbnailUrl, listProjects, type Project } from "../api/projects";
import { updateProjectVisibility } from "../api/portfolioSettings";
import { getUsername } from "../auth/user";
import {
  FeatureTile,
  PageContainer,
  PageHeader,
  SectionCard,
} from "../components/shared";

export default function ProjectsPage() {
  const username = getUsername();
  const nav = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [thumbnails, setThumbnails] = useState<Record<number, string | null>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState<number | null>(null);

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
              : p,
          ),
        );
      } catch {
        // state stays unchanged on error
      } finally {
        setToggling(null);
      }
    },
    [toggling],
  );

  return (
    <>
      <TopBar showNav username={username} />
      <PageContainer className="flex flex-col gap-[20px]">
        <PageHeader
          title="Projects"
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "Projects" },
          ]}
        />

        {loading && (
          <SectionCard>
            <p className="text-[14px] text-[#7f7f7f]">Loading…</p>
          </SectionCard>
        )}

        {error && (
          <SectionCard>
            <p className="text-[14px] text-[#cc4b4b]">{error}</p>
          </SectionCard>
        )}

        {!loading && !error && projects.length === 0 && (
          <SectionCard>
            <p className="text-[14px] text-[#7f7f7f]">
              No projects yet. Upload one to get started.
            </p>
          </SectionCard>
        )}

        {!loading && !error && projects.length > 0 && (
          <SectionCard>
            <div className="flex flex-wrap gap-[20px]">
              {projects.map((p) => (
                <div key={p.project_summary_id} className="relative">
                  <FeatureTile
                    title={p.project_name}
                    thumbnailUrl={thumbnails[p.project_summary_id]}
                    onClick={() => nav(`/projects/${p.project_summary_id}`)}
                  />
                  <button
                    className="absolute right-[8px] top-[8px] z-10 rounded-full border px-[8px] py-[2px] text-[11px] font-medium leading-none transition disabled:opacity-50"
                    style={
                      p.is_public
                        ? {
                            background: "rgba(220,252,231,0.95)",
                            borderColor: "#16a34a",
                            color: "#15803d",
                          }
                        : {
                            background: "rgba(255,255,255,0.92)",
                            borderColor: "#d1d5db",
                            color: "#6b7280",
                          }
                    }
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
          </SectionCard>
        )}
      </PageContainer>
    </>
  );
}
