import { useEffect, useState } from "react";
import {
  listResumes,
  deleteResume,
  downloadResumeDocx,
  downloadResumePdf,
  type ResumeListItem,
} from "../../api/outputs";
import ExportDropdown from "./ExportDropdown";

type Props = {
  onBack: () => void;
  onView: (id: number) => void;
  onCreateNew: () => void;
};

export default function ResumeList({ onBack, onView, onCreateNew }: Props) {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setErr(null);
    listResumes()
      .then((r) => setResumes(r.data?.resumes ?? []))
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleDelete(id: number) {
    if (!confirm("Delete this resume?")) return;
    try {
      await deleteResume(id);
      load();
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function handleExportDocx(id: number) {
    try {
      await downloadResumeDocx(id);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function handleExportPdf(id: number) {
    try {
      await downloadResumePdf(id);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  function formatDate(iso: string | null) {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  }

  return (
    <div className="content">
      <div className="outputsHeader">
        <button className="backBtn" onClick={onBack}>
          &larr;
        </button>
        <h2>Resume Items</h2>
        <button className="primaryBtn" onClick={onCreateNew}>
          Create New Resume
        </button>
      </div>

      <hr className="divider" />

      {loading && <p>Loading...</p>}
      {err && <p className="error">{err}</p>}

      {!loading && resumes.length === 0 && (
        <p className="hint">No resumes yet. Create one to get started.</p>
      )}

      <div className="resumeCards">
        {resumes.map((r) => (
          <div key={r.id} className="resumeRow">
            <div className="resumeInfo">
              <span className="resumeName">{r.name}</span>
              <span className="resumeDate">{formatDate(r.created_at)}</span>
            </div>
            <div className="resumeActions">
              <ExportDropdown
                onDocx={() => handleExportDocx(r.id)}
                onPdf={() => handleExportPdf(r.id)}
              />
              <button className="actionBtn dark" onClick={() => onView(r.id)}>
                View
              </button>
              <button className="actionBtn outline" onClick={() => onView(r.id)}>
                Edit
              </button>
              <button
                className="actionBtn outline danger"
                onClick={() => handleDelete(r.id)}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
