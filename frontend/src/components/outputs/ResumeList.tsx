import { useEffect, useState } from "react";
import {
  listResumes,
  deleteResume,
  downloadResumeDocx,
  downloadResumePdf,
  type ResumeListItem,
} from "../../api/outputs";
import ExportDropdown from "./ExportDropdown";
import { Button } from "@/components/ui/button";
import { Plus, Eye, Pencil, Trash2 } from "lucide-react";

type Props = {
  onView: (id: number) => void;
  onEdit: (id: number) => void;
  onCreateNew: () => void;
};

export default function ResumeList({ onView, onEdit, onCreateNew }: Props) {
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
    <div className="p-6">
      <div className="flex justify-end">
        <Button size="sm" onClick={onCreateNew} className="gap-1.5">
          <Plus className="size-3.5" />
          Create New Resume
        </Button>
      </div>

      <hr className="my-4 border-t border-[#e5e5e5]" />

      {loading && <p className="text-sm text-[#7f7f7f]">Loading...</p>}
      {err && <p className="text-sm text-[#cc4b4b]">{err}</p>}

      {!loading && resumes.length === 0 && (
        <p className="text-sm text-[#7f7f7f]">No resumes yet. Create one to get started.</p>
      )}

      <div className="flex flex-col gap-3">
        {resumes.map((r) => (
          <div
            key={r.id}
            className="flex items-center justify-between rounded-xl border border-[#e5e5e5] bg-white px-5 py-4"
          >
            <div className="flex flex-col gap-0.5">
              <span className="text-[15px] font-semibold text-foreground">{r.name}</span>
              <span className="text-xs italic text-[#7f7f7f]">{formatDate(r.created_at)}</span>
            </div>
            <div className="flex items-center gap-2">
              <ExportDropdown
                onDocx={() => handleExportDocx(r.id)}
                onPdf={() => handleExportPdf(r.id)}
              />
              <Button variant="default" size="sm" onClick={() => onView(r.id)} className="gap-1.5">
                <Eye className="size-3.5" />
                View
              </Button>
              <Button variant="outline" size="sm" onClick={() => onEdit(r.id)} className="gap-1.5">
                <Pencil className="size-3.5" />
                Edit
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => handleDelete(r.id)}
                className="gap-1.5"
              >
                <Trash2 className="size-3.5" />
                Delete
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
