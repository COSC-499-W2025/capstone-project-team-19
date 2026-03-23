import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import PublicLayout from "./PublicLayout";
import { publicGetActiveResume, publicDownloadResumeDocx, publicDownloadResumePdf } from "../../api/public";
import type { PublicResumeDetail, PublicResumeProject } from "../../api/public";
import ExportDropdown from "../../components/outputs/ExportDropdown";

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

function ResumeView({ resume, username }: { resume: PublicResumeDetail; username: string }) {
    const agg = resume.aggregated_skills;
    const sortedProjects = sortProjectsByDate(resume.projects);

    return (
        <div className="p-7">
            <div className="flex items-center gap-3">
                <h2 className="flex-1 m-0">{resume.name}</h2>
                <ExportDropdown
                    onDocx={() => publicDownloadResumeDocx(username, resume.id)}
                    onPdf={() => publicDownloadResumePdf(username, resume.id)}
                />
            </div>

            <hr className="border-0 border-t border-[var(--border)] my-4" />

            <div className="mt-6 py-4 px-5 bg-[var(--card)] border border-[var(--border)] rounded-xl">
                <h3 className="m-0 mb-2 text-base border-b border-[var(--border)] pb-1">Skills</h3>
                {agg.languages.length > 0 && (
                    <p className="my-1 text-sm"><strong>Languages:</strong> {agg.languages.join(", ")}</p>
                )}
                {agg.frameworks.length > 0 && (
                    <p className="my-1 text-sm"><strong>Frameworks:</strong> {agg.frameworks.join(", ")}</p>
                )}
                {agg.technical_skills.length > 0 && (
                    <p className="my-1 text-sm"><strong>Technical skills:</strong> {agg.technical_skills.join(", ")}</p>
                )}
                {agg.writing_skills.length > 0 && (
                    <p className="my-1 text-sm"><strong>Writing skills:</strong> {agg.writing_skills.join(", ")}</p>
                )}
            </div>

            <div>
                <h3 className="text-base font-bold mt-5 mb-2 pb-1 border-b border-[var(--border)]">Projects</h3>
                {sortedProjects.map((p, i) => {
                    const dateLine = formatDateRange(p.start_date, p.end_date);
                    const subtitle = p.key_role && dateLine
                        ? `${p.key_role} | ${dateLine}`
                        : p.key_role || dateLine;
                    return (
                        <div key={i} className="bg-[var(--card)] border border-[var(--border)] rounded-xl py-4 px-5 mb-[10px] shadow-sm">
                            <div>
                                <h4 className="m-0 mb-1.5 text-[15px] font-bold">{p.project_name}</h4>
                                {subtitle && (
                                    <p className="my-0.5 pl-4 text-sm leading-[1.5] italic">{subtitle}</p>
                                )}
                                {p.contribution_bullets.length > 0 && (
                                    <ul className="my-0.5 pl-6 list-disc">
                                        {p.contribution_bullets.map((b, j) => (
                                            <li key={j} className="text-sm leading-[1.5]">{b}</li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        </div>
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
            {loading ? (
                <div className="p-7"><p>Loading...</p></div>
            ) : error ? (
                <div className="p-7"><p className="text-[#b00020] text-xs">{error}</p></div>
            ) : !resume ? (
                <div className="p-7"><p>No resume has been set for this portfolio.</p></div>
            ) : (
                <ResumeView resume={resume} username={username!} />
            )}
        </PublicLayout>
    );
}
