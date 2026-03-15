import { Button } from "@/components/ui/button";

type Props = {
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  isSubmitting: boolean;
};

export default function SetupAnalyzeConfirmDialog({ open, onCancel, onConfirm, isSubmitting }: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-5 shadow-xl">
        <h3 className="text-base font-semibold text-zinc-900">Confirm Analysis Start</h3>
        <p className="mt-2 text-sm leading-relaxed text-zinc-700">
          Please confirm your setup details are correct. Once analysis starts, setup selections should not be changed.
        </p>
        <p className="mt-2 text-xs text-zinc-600">
          You can still review progress in Step 4 (Analyze), but setup edits are not guaranteed to be applied.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="button" onClick={onConfirm} disabled={isSubmitting}>
            {isSubmitting ? "Starting..." : "Start Analysis"}
          </Button>
        </div>
      </div>
    </div>
  );
}
