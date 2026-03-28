import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import PublicLayout from "./PublicLayout";
import {
  publicGetProject,
  publicFetchThumbnailUrl,
  publicListProjects,
} from "../../api/public";
import type { PublicProjectDetail, PublicProject } from "../../api/public";
import {
  AppButton,
  PageContainer,
  PageHeader,
  SectionCard,
  SectionTabs,
  TagPill,
} from "../../components/shared";

export default function PublicProjectDetailPage() {
  const { username, id } = useParams<{ username: string; id: string }>();
  const projectId = Number(id);
  const nav = useNavigate();

  const [project, setProject] = useState<PublicProjectDetail | null>(null);
  const [thumbUrl, setThumbUrl] = useState<string | null>(null);
  const [allProjects, setAllProjects] = useState<PublicProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("summary");

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

  function formatDate(d: string | null | undefined) {
    if (!d) return "—";
    return d;
  }

  function formatSkillName(s: string) {
    return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  const basePath = `/public/${username}/projects`;

  const hasSkills =
    project &&
    (project.languages?.length > 0 ||
      project.frameworks?.length > 0 ||
      project.skills?.length > 0);

  if (loading) {
    return (
      <PublicLayout>
        <PageContainer>
          <p className="text-[14px] text-[#7f7f7f]">Loading…</p>
        </PageContainer>
      </PublicLayout>
    );
  }

  if (error || !project) {
    return (
      <PublicLayout>
        <PageContainer className="flex flex-col gap-[20px]">
          <p className="text-[14px] text-[#cc4b4b]">
            {error ?? "Project not found."}
          </p>
          <div>
            <AppButton variant="ghost" onClick={() => nav(basePath)}>
              ← Back to Projects
            </AppButton>
          </div>
        </PageContainer>
      </PublicLayout>
    );
  }

  const currentIndex = allProjects.findIndex(
    (p) => p.project_summary_id === projectId,
  );
  const prevProject = currentIndex > 0 ? allProjects[currentIndex - 1] : null;
  const nextProject =
    currentIndex !== -1 && currentIndex < allProjects.length - 1
      ? allProjects[currentIndex + 1]
      : null;

  const tabs = [
    { key: "summary", label: "Summary" },
    ...(hasSkills ? [{ key: "skills", label: "Skills & Technologies" }] : []),
  ];

  return (
    <PublicLayout>
      <PageContainer className="flex flex-col gap-[20px]">
        <PageHeader
          title={project.project_name}
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "Projects", href: basePath },
            { label: project.project_name },
          ]}
        />

        {/* Thumbnail + Meta */}
        <SectionCard>
          <div className="flex gap-[20px]">
            <div className="shrink-0">
              <div
                className="h-[140px] w-[186px] overflow-hidden rounded-[6px] bg-[#ebebeb] bg-cover bg-center"
                style={
                  thumbUrl
                    ? { backgroundImage: `url(${thumbUrl})` }
                    : undefined
                }
              >
                {!thumbUrl && (
                  <div className="flex h-full items-center justify-center text-[13px] text-[#9f9f9f]">
                    No Image
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-wrap gap-[8px] self-start">
              {project.project_type && (
                <TagPill className="capitalize">{project.project_type}</TagPill>
              )}
              {project.project_mode && (
                <TagPill className="capitalize">{project.project_mode}</TagPill>
              )}
            </div>
          </div>
        </SectionCard>

        {/* Duration */}
        {(project.start_date || project.end_date) && (
          <SectionCard className="space-y-[14px]">
            <div className="text-[18px] font-medium leading-none text-foreground">
              Duration
            </div>
            <span className="text-[14px] text-foreground">
              {formatDate(project.start_date)} → {formatDate(project.end_date)}
            </span>
          </SectionCard>
        )}

        {/* Summary / Skills tabs */}
        <SectionCard className="space-y-[16px]">
          <SectionTabs
            tabs={tabs}
            activeKey={activeTab}
            onChange={setActiveTab}
            align="left"
          />

          {activeTab === "summary" && (
            <div className="space-y-[14px]">
              <div className="text-[18px] font-medium text-foreground">
                Project Summary
              </div>
              <div className="space-y-[6px]">
                <div className="text-[13px] font-semibold text-muted-foreground uppercase tracking-wide">
                  Summary
                </div>
                <div className="rounded-[8px] border border-border bg-muted/30 p-[14px]">
                  <p className="whitespace-pre-wrap text-[14px] leading-[1.7] text-foreground">
                    {project.summary_text ? (
                      project.summary_text
                    ) : (
                      <span className="italic text-muted-foreground">No summary available.</span>
                    )}
                  </p>
                </div>
              </div>
              {project.project_mode === "collaborative" && (
                <div className="space-y-[6px]">
                  <div className="text-[13px] font-semibold text-muted-foreground uppercase tracking-wide">
                    Contribution Summary
                  </div>
                  <div className="rounded-[8px] border border-border bg-muted/30 p-[14px]">
                    <p className="whitespace-pre-wrap text-[14px] leading-[1.7] text-foreground">
                      {project.contribution_summary ? (
                        project.contribution_summary
                      ) : (
                        <span className="italic text-muted-foreground">No contribution summary available.</span>
                      )}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "skills" && hasSkills && (
            <div className="space-y-[12px]">
              {project.languages?.length > 0 && (
                <div className="space-y-[6px]">
                  <div className="text-[14px] font-medium text-foreground">
                    Languages
                  </div>
                  <div className="flex flex-wrap gap-[8px]">
                    {project.languages.map((l) => (
                      <TagPill key={l}>{l}</TagPill>
                    ))}
                  </div>
                </div>
              )}
              {project.frameworks?.length > 0 && (
                <div className="space-y-[6px]">
                  <div className="text-[14px] font-medium text-foreground">
                    Frameworks
                  </div>
                  <div className="flex flex-wrap gap-[8px]">
                    {project.frameworks.map((f) => (
                      <TagPill key={f}>{f}</TagPill>
                    ))}
                  </div>
                </div>
              )}
              {project.skills?.length > 0 && (
                <div className="space-y-[6px]">
                  <div className="text-[14px] font-medium text-foreground">
                    Skills
                  </div>
                  <div className="flex flex-wrap gap-[8px]">
                    {project.skills.map((s) => (
                      <TagPill key={s}>{formatSkillName(s)}</TagPill>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </SectionCard>

        {/* Prev/Next navigation */}
        {(prevProject || nextProject) && (
          <div className="flex justify-between">
            {prevProject ? (
              <AppButton
                variant="ghost"
                onClick={() =>
                  nav(`${basePath}/${prevProject.project_summary_id}`)
                }
              >
                ← {prevProject.project_name}
              </AppButton>
            ) : (
              <span />
            )}
            {nextProject && (
              <AppButton
                variant="ghost"
                onClick={() =>
                  nav(`${basePath}/${nextProject.project_summary_id}`)
                }
              >
                {nextProject.project_name} →
              </AppButton>
            )}
          </div>
        )}
      </PageContainer>
    </PublicLayout>
  );
}
