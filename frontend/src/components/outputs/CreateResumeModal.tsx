import { useEffect, useState } from "react";
import {
  getRankedProjects,
  createResume,
  type RankedProject,
} from "../../api/outputs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { X, Pencil } from "lucide-react";

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="relative w-full max-w-lg rounded-2xl border border-[#e5e5e5] bg-white shadow-lg">
        {/* Close button */}
        <Button
          variant="ghost"
          size="icon-sm"
          className="absolute right-3 top-3 text-slate-400 hover:text-slate-700"
          onClick={onClose}
        >
          <X className="size-4" />
        </Button>

        <div className="px-6 pt-6 pb-2">
          {/* Title input */}
          <div className="flex items-center gap-2 w-1/2">
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Resume Title"
              className="text-lg font-semibold"
            />
            <Pencil className="size-4 text-slate-400" />
          </div>
        </div>

        <Separator />

        <div className="px-6 py-4">
          <Label className="text-sm font-medium text-slate-900">Available Projects</Label>

          {loading && <p className="mt-3 text-sm text-[#7f7f7f]">Loading projects...</p>}
          {err && <p className="mt-3 text-sm text-[#cc4b4b]">{err}</p>}

          {!loading && projects.length === 0 && (
            <p className="mt-3 text-sm text-[#7f7f7f]">
              No projects found. Upload a project first.
            </p>
          )}

          {projects.length > 0 && (
            <div className="mt-3 max-h-64 overflow-y-auto rounded-lg border border-slate-200">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-50">
                  <tr className="border-b border-slate-200">
                    <th className="w-10 py-2 pl-3"></th>
                    <th className="py-2 text-left font-medium text-slate-600">Project</th>
                    <th className="py-2 pr-3 text-right font-medium text-slate-600">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr
                      key={p.project_summary_id}
                      className="cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50"
                      onClick={() => toggleProject(p.project_summary_id)}
                    >
                      <td className="py-2 pl-3">
                        <input
                          type="checkbox"
                          checked={selected.has(p.project_summary_id)}
                          onChange={() => toggleProject(p.project_summary_id)}
                          onClick={(e) => e.stopPropagation()}
                          className="size-4 rounded border-slate-300"
                        />
                      </td>
                      <td className="py-2 text-slate-700">{p.project_name}</td>
                      <td className="py-2 pr-3 text-right text-slate-500">{p.score.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <Separator />

        <div className="flex justify-end px-6 py-4">
          <Button
            onClick={handleCreate}
            disabled={creating}
          >
            {creating ? "Creating..." : "Create Resume"}
          </Button>
        </div>
      </div>
    </div>
  );
}
