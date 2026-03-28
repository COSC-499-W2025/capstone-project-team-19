import { useEffect, useState } from "react";
import { getRankedProjects, addProjectToResume, type RankedProject } from "../../api/outputs";

type Props = {
  resumeId: number;
  currentProjectNames: string[];
  onClose: () => void;
  onAdded: () => void;
};

export default function AddProjectModal({
  resumeId,
  currentProjectNames,
  onClose,
  onAdded,
}: Props) {
  const [projects, setProjects] = useState<RankedProject[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getRankedProjects()
      .then((r) => setProjects(r.data?.rankings ?? []))
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, []);

  const available = projects.filter(
    (p) => !currentProjectNames.includes(p.project_name)
  );

  function toggleProject(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleAdd() {
    if (selected.size === 0) return;
    setAdding(true);
    setErr(null);
    try {
      for (const id of selected) {
        await addProjectToResume(resumeId, id);
      }
      onAdded();
      onClose();
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="modalOverlay">
      <div className="modalContent">
        <button className="modalClose" onClick={onClose}>
          &times;
        </button>
        <h3>Add Project</h3>
        {loading && <p>Loading projects...</p>}
        {err && <p className="error">{err}</p>}
        {!loading && available.length === 0 && (
          <p className="hint">No projects to add. All projects are already in this resume.</p>
        )}
        {available.length > 0 && (
          <table className="projectTable">
            <thead>
              <tr>
                <th></th>
                <th>Project</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {available.map((p) => (
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
        <div className="modalFooter addProjectModalFooter">
          <button className="addProjectModalFooter__cancel" onClick={onClose} type="button">
            Cancel
          </button>
          <button
            className="addProjectModalFooter__add"
            onClick={handleAdd}
            disabled={adding || selected.size === 0}
            type="button"
          >
            {adding ? "Adding..." : "Add"}
          </button>
        </div>
      </div>
    </div>
  );
}
