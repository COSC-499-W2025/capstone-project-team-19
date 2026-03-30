import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import PublicLayout from "./PublicLayout";
import { publicGetActiveResume, publicDownloadResumeDocx, publicDownloadResumePdf } from "../../api/public";
import type { PublicResumeDetail, PublicResumeProject } from "../../api/public";
import ExportDropdown from "../../components/outputs/ExportDropdown";
import { PageContainer, PageHeader, SectionCard } from "../../components/shared";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

function formatDateRange(start: string | null, end: string | null): string {
    const fmt = (iso: string) => {
        const d = new Date(iso);
        if (isNaN(d.getTime())) return "";
        return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
    };
    const s = start ? fmt(start) : "";
    const e = end ? fmt(end) : "";
    if (s && e) return `${s} \u2013 ${e}`;
    if (s) return `${s} \u2013 Present`;
    if (e) return e;
    return "";
}

function sortProjectsByDate(projects: PublicResumeProject[]): PublicResumeProject[] {
    return [...projects].sort((a, b) => {
        const dateA = a.end_date || a.start_date || "";
        const dateB = b.end_date || b.start_date || "";
        if (!dateA && !dateB) return 0;
        if (!dateA) return 1;
        if (!dateB) return -1;
        return dateB.localeCompare(dateA);
    });
}

function SkillRow({ label, items }: { label: string; items: string[] }) {
    if (items.length === 0) return null;
    return (
        <p className="text-sm text-slate-700">
            <span className="font-medium">{label}:</span> {items.join(", ")}
        </p>
    );
}

function ResumeView({ resume, username }: { resume: PublicResumeDetail; username: string }) {
    const agg = resume.aggregated_skills;
    const sortedProjects = sortProjectsByDate(resume.projects);

    return (
        <div className="p-6">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-foreground">{resume.name}</h2>
                <ExportDropdown
                    onDocx={() => publicDownloadResumeDocx(username, resume.id)}
                    onPdf={() => publicDownloadResumePdf(username, resume.id)}
                />
            </div>

            <hr className="my-4 border-t border-[#e5e5e5]" />

            {/* Skills Summary */}
            <Card className="mb-6 rounded-2xl border-slate-200/80 bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-base text-slate-900">Skills</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                    <SkillRow label="Languages" items={agg.languages} />
                    <SkillRow label="Frameworks" items={agg.frameworks} />
                    <SkillRow label="Technical" items={agg.technical_skills} />
                    <SkillRow label="Writing" items={agg.writing_skills} />
                </CardContent>
            </Card>

            {/* Projects */}
            <div className="space-y-4">
                <h3 className="border-b border-[#e5e5e5] pb-1 text-base font-semibold text-slate-900">
                    Projects
                </h3>
                {sortedProjects.map((p, i) => {
                    const dateLine = formatDateRange(p.start_date, p.end_date);
                    const subtitle = p.key_role && dateLine
                        ? `${p.key_role} | ${dateLine}`
                        : p.key_role || dateLine;
                    return (
                        <Card key={i} className="rounded-xl border-slate-200/80 bg-white shadow-sm">
                            <CardContent className="py-4">
                                <h4 className="text-[15px] font-semibold text-slate-900">{p.project_name}</h4>
                                {subtitle && (
                                    <p className="mt-0.5 text-sm italic text-slate-500">{subtitle}</p>
                                )}
                                {p.contribution_bullets.length > 0 && (
                                    <ul className="mt-1.5 list-disc space-y-0.5 pl-5">
                                        {p.contribution_bullets.map((b, j) => (
                                            <li key={j} className="text-sm leading-relaxed text-slate-700">{b}</li>
                                        ))}
                                    </ul>
                                )}
                            </CardContent>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
}

export default function PublicOutputsPage() {
    const { username } = useParams<{ username: string }>();
    const [resume, setResume] = useState<PublicResumeDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!username) return;
        publicGetActiveResume(username)
            .then(setResume)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, [username]);

    return (
        <PublicLayout>
            <PageContainer className="flex min-h-[calc(100vh-64px)] flex-col gap-[20px] bg-background pt-[12px]">
                <PageHeader
                    title="Resume"
                    breadcrumbs={[{ label: "Home", href: "/" }, { label: "Resume" }]}
                />
                <SectionCard className="flex w-full flex-1 flex-col bg-white">
                    {loading ? (
                        <p className="text-[14px] text-[#7f7f7f]">Loading...</p>
                    ) : error ? (
                        <p className="text-[14px] text-[#cc4b4b]">{error}</p>
                    ) : !resume ? (
                        <p className="text-[14px] text-[#7f7f7f]">No resume has been set for this portfolio.</p>
                    ) : (
                        <ResumeView resume={resume} username={username!} />
                    )}
                </SectionCard>
            </PageContainer>
        </PublicLayout>
    );
}
