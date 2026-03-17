import { useEffect, useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import PublicLayout from "./PublicLayout";
import { publicListProjects, publicFetchThumbnailUrl, type PublicProject } from "../../api/public";
import {
  FeatureTile,
  PageContainer,
  PageHeader,
  SectionCard,
} from "../../components/shared";

export default function PublicProjectsPage() {
  const { username } = useParams<{ username: string }>();
  const nav = useNavigate();
  const [projects, setProjects] = useState<PublicProject[]>([]);
  const [thumbnails, setThumbnails] = useState<Record<number, string | null>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const thumbnailFetcher = useCallback(
    (projectId: number) => publicFetchThumbnailUrl(username!, projectId),
    [username],
  );

  useEffect(() => {
    if (!username) return;
    let cancelled = false;
    const objectUrls: string[] = [];

    publicListProjects(username)
      .then((list) => {
        if (cancelled) return;
        setProjects(list);
        Promise.all(
          list.map((p) =>
            thumbnailFetcher(p.project_summary_id).then((url) => ({
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
  }, [username, thumbnailFetcher]);

  return (
    <PublicLayout>
      <PageContainer className="flex flex-col gap-[20px]">
        <PageHeader
          title="Projects"
          breadcrumbs={[{ label: "Home", href: "/" }, { label: "Projects" }]}
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
            <p className="text-[14px] text-[#7f7f7f]">No projects yet.</p>
          </SectionCard>
        )}

        {!loading && !error && projects.length > 0 && (
          <SectionCard>
            <div className="flex flex-wrap gap-[20px]">
              {projects.map((p) => (
                <FeatureTile
                  key={p.project_summary_id}
                  title={p.project_name}
                  thumbnailUrl={thumbnails[p.project_summary_id]}
                  onClick={() =>
                    nav(`/public/${username}/projects/${p.project_summary_id}`)
                  }
                />
              ))}
            </div>
          </SectionCard>
        )}
      </PageContainer>
    </PublicLayout>
  );
}
