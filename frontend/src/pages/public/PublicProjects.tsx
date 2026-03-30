import { useEffect, useState, useCallback, useMemo } from "react";
import { ChevronRight } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import PublicLayout from "./PublicLayout";
import {
  publicListProjects,
  publicFetchThumbnailUrl,
  publicGetRanking,
  type PublicProject,
  type PublicRankingItem,
} from "../../api/public";
import {
  FeatureTile,
  PageContainer,
  PageHeader,
  SectionCard,
} from "../../components/shared";

const TOP_FEATURED = 3;

export default function PublicProjectsPage() {
  const { username } = useParams<{ username: string }>();
  const nav = useNavigate();
  const [projects, setProjects] = useState<PublicProject[]>([]);
  const [rankings, setRankings] = useState<PublicRankingItem[]>([]);
  const [thumbnails, setThumbnails] = useState<Record<number, string | null>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const thumbnailFetcher = useCallback(
    (projectId: number) => publicFetchThumbnailUrl(username!, projectId),
    [username],
  );

  const projectIdSet = useMemo(
    () => new Set(projects.map((p) => p.project_summary_id)),
    [projects],
  );

  const topFeatured = useMemo(() => {
    const ordered = rankings.filter((r) => projectIdSet.has(r.project_summary_id));
    return ordered.slice(0, TOP_FEATURED);
  }, [rankings, projectIdSet]);

  const topFeaturedIds = useMemo(() => new Set(topFeatured.map((r) => r.project_summary_id)), [topFeatured]);

  const moreProjects = useMemo(
    () => projects.filter((p) => !topFeaturedIds.has(p.project_summary_id)),
    [projects, topFeaturedIds],
  );

  useEffect(() => {
    if (!username) return;
    let cancelled = false;
    const objectUrls: string[] = [];

    Promise.all([publicListProjects(username), publicGetRanking(username).catch(() => [])])
      .then(([list, rankList]) => {
        if (cancelled) return;
        setProjects(list);
        setRankings(rankList);
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
      <PageContainer className="flex min-h-[calc(100vh-64px)] flex-col gap-[20px] bg-background pt-[12px]">
        <PageHeader
          title="Projects"
          breadcrumbs={[{ label: "Home", href: "/" }, { label: "Projects" }]}
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
            <p className="text-[14px] text-[#7f7f7f]">No projects yet.</p>
          </SectionCard>
        )}

        {!loading && !error && projects.length > 0 && (
          <>
            <p className="m-0 text-[14px] leading-snug text-[#7f7f7f]">
              See skill evolution, ranked work, and activity over time on{" "}
              <Link
                to={`/public/${username}/insights`}
                className="font-medium text-[#001166] underline underline-offset-2 hover:text-[#001a8c]"
              >
                Insights
              </Link>
              .
            </p>

            {topFeatured.length > 0 && (
              <SectionCard>
                <h2 className="m-0 mb-1 text-[18px] font-semibold leading-tight text-[#3a3a3a]">
                  Top projects
                </h2>
                <p className="mb-4 mt-0 text-[14px] leading-snug text-[#7f7f7f]">
                  Highest-scoring public projects on this portfolio (up to three).
                </p>
                <div className="flex flex-wrap gap-[20px]">
                  {topFeatured.map((r) => (
                    <div
                      key={r.project_summary_id}
                      className="flex w-[220px] flex-col items-stretch gap-2"
                    >
                      <FeatureTile
                        title={r.project_name}
                        thumbnailUrl={thumbnails[r.project_summary_id]}
                        featuredRank={r.rank as 1 | 2 | 3}
                        aria-label={`Top ${r.rank}: ${r.project_name}`}
                        onClick={() =>
                          nav(`/public/${username}/projects/${r.project_summary_id}`)
                        }
                      />
                      <Link
                        to={`/public/${username}/insights?view=activity-heatmap&project=${r.project_summary_id}`}
                        className="group flex w-full items-center justify-between gap-2 rounded-md border border-[#001166]/20 bg-[#f5f7fb] px-[14px] py-2.5 text-left text-[13px] font-semibold leading-tight text-[#001166] shadow-sm outline-none ring-[#001166]/15 transition hover:border-[#001166]/40 hover:bg-[#e8ecf7] hover:shadow-md focus-visible:ring-2 active:translate-y-px"
                      >
                        <span className="min-w-0 text-left">Activity insights</span>
                        <ChevronRight
                          className="h-4 w-4 shrink-0 text-[#001166] opacity-70 transition group-hover:translate-x-0.5 group-hover:opacity-100"
                          aria-hidden
                          strokeWidth={2.25}
                        />
                      </Link>
                    </div>
                  ))}
                </div>
              </SectionCard>
            )}

            {moreProjects.length > 0 && (
              <SectionCard>
                <h2 className="m-0 mb-4 text-[18px] font-semibold leading-tight text-[#3a3a3a]">
                  {topFeatured.length > 0 ? "More projects" : "All projects"}
                </h2>
                <div className="flex flex-wrap gap-[20px]">
                  {moreProjects.map((p) => (
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
          </>
        )}
      </PageContainer>
    </PublicLayout>
  );
}
