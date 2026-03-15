import { Button } from "@/components/ui/button";

type Props = {
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

export default function SetupAnalyzeConfirmDialog({ open, onCancel, onConfirm }: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-5 shadow-xl">
        <h3 className="text-base font-semibold text-zinc-900">Confirm Before Continue</h3>
        <p className="mt-2 text-sm leading-relaxed text-zinc-700">
          Please confirm your setup details are correct before moving to Analyze.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="button" onClick={onConfirm} className="bg-black text-white hover:bg-zinc-800">
            Continue
          </Button>
        </div>
      </div>
    </div>
  );
}
