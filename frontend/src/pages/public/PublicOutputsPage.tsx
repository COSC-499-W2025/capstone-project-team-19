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
        <div className="content">
            <div className="outputsHeader">
                <h2>{resume.name}</h2>
                <ExportDropdown
                    onDocx={() => publicDownloadResumeDocx(username, resume.id)}
                    onPdf={() => publicDownloadResumePdf(username, resume.id)}
                />
            </div>

            <hr className="divider" />

            <div className="skillsSummaryBlock">
                <h3>Skills</h3>
                {agg.languages.length > 0 && (
                    <p><strong>Languages:</strong> {agg.languages.join(", ")}</p>
                )}
                {agg.frameworks.length > 0 && (
                    <p><strong>Frameworks:</strong> {agg.frameworks.join(", ")}</p>
                )}
                {agg.technical_skills.length > 0 && (
                    <p><strong>Technical skills:</strong> {agg.technical_skills.join(", ")}</p>
                )}
                {agg.writing_skills.length > 0 && (
                    <p><strong>Writing skills:</strong> {agg.writing_skills.join(", ")}</p>
                )}
            </div>

            <div className="resumeProjectsList">
                <h3 className="groupHeader">Projects</h3>
                {sortedProjects.map((p, i) => {
                    const dateLine = formatDateRange(p.start_date, p.end_date);
                    const subtitle = p.key_role && dateLine
                        ? `${p.key_role} | ${dateLine}`
                        : p.key_role || dateLine;
                    return (
                        <div key={i} className="resumeProjectBlock">
                            <div className="projectBlockContent">
                                <h4 className="projectBlockName">{p.project_name}</h4>
                                {subtitle && (
                                    <p className="projectField" style={{ fontStyle: "italic" }}>{subtitle}</p>
                                )}
                                {p.contribution_bullets.length > 0 && (
                                    <ul className="bulletList">
                                        {p.contribution_bullets.map((b, j) => (
                                            <li key={j}>{b}</li>
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
                <div className="content"><p>Loading...</p></div>
            ) : error ? (
                <div className="content"><p className="error">{error}</p></div>
            ) : !resume ? (
                <div className="content"><p>No resume has been set for this portfolio.</p></div>
            ) : (
                <ResumeView resume={resume} username={username!} />
            )}
        </PublicLayout>
    );
}
