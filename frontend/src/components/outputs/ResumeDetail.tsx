import { useEffect, useState } from "react";
import {
  getResume,
  downloadResumeDocx,
  downloadResumePdf,
  type ResumeDetail as ResumeDetailType,
  type ResumeProject,
} from "../../api/outputs";
import ExportDropdown from "./ExportDropdown";

type Props = {
  resumeId: number;
  onBack: () => void;
};

/** Group projects by "code (individual)", "text (collaborative)", etc. */
function groupProjects(projects: ResumeProject[]) {
  const groups: Record<string, ResumeProject[]> = {};
  for (const p of projects) {
    const type = p.project_type ?? "other";
    const mode = p.project_mode ?? "";
    const key = mode ? `${type} (${mode})` : type;
    (groups[key] ??= []).push(p);
  }
  return groups;
}

function formatGroupLabel(key: string) {
  return key.charAt(0).toUpperCase() + key.slice(1) + " Projects";
}

export default function ResumeDetail({ resumeId, onBack }: Props) {
  const [resume, setResume] = useState<ResumeDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getResume(resumeId)
      .then((r) => setResume(r.data))
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [resumeId]);

  async function handleExportDocx() {
    try {
      await downloadResumeDocx(resumeId);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function handleExportPdf() {
    try {
      await downloadResumePdf(resumeId);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  if (loading) return <div className="content"><p>Loading...</p></div>;
  if (err) return <div className="content"><p className="error">{err}</p></div>;
  if (!resume) return <div className="content"><p>Resume not found.</p></div>;

  const grouped = groupProjects(resume.projects);
  const agg = resume.aggregated_skills;

  return (
    <div className="content">
      <div className="outputsHeader">
        <button className="backBtn" onClick={onBack}>&larr;</button>
        <h2>{resume.name}</h2>
        <ExportDropdown onDocx={handleExportDocx} onPdf={handleExportPdf} />
      </div>

      <hr className="divider" />

      {/* Projects grouped by type/mode, matching CLI layout */}
      {Object.entries(grouped).map(([groupKey, projects]) => (
        <div key={groupKey} className="resumeGroup">
          <h3 className="groupHeader">{formatGroupLabel(groupKey)}</h3>

          {projects.map((p, i) => (
            <div key={i} className="resumeProjectBlock">
              <ProjectBlock project={p} />
            </div>
          ))}
        </div>
      ))}

      {/* Aggregated skills summary */}
      <div className="skillsSummaryBlock">
        <h3>Skills Summary</h3>
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
    </div>
  );
}

function ProjectBlock({ project: p }: { project: ResumeProject }) {
  return (
    <div className="projectBlockContent">
      <h4 className="projectBlockName">{p.project_name}</h4>

      {p.key_role && <p className="projectField">Role: {p.key_role}</p>}

      {p.languages.length > 0 && (
        <p className="projectField">Languages: {p.languages.join(", ")}</p>
      )}

      {p.frameworks.length > 0 && (
        <p className="projectField">Frameworks: {p.frameworks.join(", ")}</p>
      )}

      {p.text_type && (
        <p className="projectField">Type: {p.text_type}</p>
      )}

      {p.contribution_percent != null && (
        <p className="projectField">
          Contribution: {Math.round(p.contribution_percent)}%
        </p>
      )}

      {p.summary_text && (
        <p className="projectField">Summary: {p.summary_text}</p>
      )}

      {p.contribution_bullets.length > 0 && (
        <div className="projectField">
          <p>Contributions:</p>
          <ul className="bulletList">
            {p.contribution_bullets.map((b, j) => (
              <li key={j}>{b}</li>
            ))}
          </ul>
        </div>
      )}

      {p.skills.length > 0 && (
        <div className="projectField">
          <p>Skills:</p>
          <ul className="bulletList">
            <li>{p.skills.join(", ")}</li>
          </ul>
        </div>
      )}
    </div>
  );
}
