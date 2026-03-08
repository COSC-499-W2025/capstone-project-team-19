import { useEffect, useState } from "react";
import {
  getRankedProjects,
  createResume,
  type RankedProject,
} from "../../api/outputs";

type Props = {
  onClose: () => void;
  onCreated: (id: number) => void;
};

export default function CreateResumeModal({ onClose, onCreated }: Props) {
  const [title, setTitle] = useState("My Resume");
  const [projects, setProjects] = useState<RankedProject[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getRankedProjects()
      .then((r) => setProjects(r.data?.rankings ?? []))
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, []);

  function toggleProject(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleCreate() {
    if (selected.size === 0) {
      setErr("Select at least one project.");
      return;
    }
    setCreating(true);
    setErr(null);
    try {
      const res = await createResume(title, [...selected]);
      if (res.data) onCreated(res.data.id);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="modalOverlay">
      <div className="modalContent">
        <button className="modalClose" onClick={onClose}>
          &times;
        </button>

        <div className="modalHeader">
          <div className="titleRow">
            <input
              className="resumeTitleInput"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Resume Title"
            />
            <span className="editIcon">&#9998;</span>
          </div>
          <button
            className="primaryBtn"
            onClick={handleCreate}
            disabled={creating}
          >
            {creating ? "Creating..." : "Create Resume"}
          </button>
        </div>

        <hr className="divider" />

        <h3>Available Projects</h3>

        {loading && <p>Loading projects...</p>}
        {err && <p className="error">{err}</p>}

        {!loading && projects.length === 0 && (
          <p className="hint">
            No projects found. Upload a project first.
          </p>
        )}

        {projects.length > 0 && (
          <table className="projectTable">
            <thead>
              <tr>
                <th></th>
                <th>Project</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.project_summary_id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selected.has(p.project_summary_id)}
                      onChange={() => toggleProject(p.project_summary_id)}
                    />
                  </td>
                  <td>{p.project_name}</td>
                  <td>{p.score.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
