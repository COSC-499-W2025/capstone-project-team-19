import { Button } from "@/components/ui/button";

type Props = {
  open: boolean;
  title: string;
  description: string;
  cancelLabel?: string;
  confirmLabel: string;
  onCancel: () => void;
  onConfirm: () => void;
  confirmDisabled?: boolean;
  busy?: boolean;
  busyMessage?: string;
};

export default function UploadConfirmDialog({
  open,
  title,
  description,
  cancelLabel = "Cancel",
  confirmLabel,
  onCancel,
  onConfirm,
  confirmDisabled = false,
  busy = false,
  busyMessage = "Please wait...",
}: Props) {
  if (!open) return null;
  const controlsDisabled = confirmDisabled || busy;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="relative w-full max-w-md rounded-xl border border-zinc-200 bg-white p-5 shadow-xl">
        <button
          type="button"
          onClick={onCancel}
          disabled={controlsDisabled}
          aria-label="Close dialog"
          className="absolute right-3 top-3 inline-flex h-7 w-7 items-center justify-center rounded-md border border-zinc-200 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          ×
        </button>
        <h3 className="pr-8 text-base font-semibold text-zinc-900">{title}</h3>
        <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-zinc-700">{description}</p>
        {busy && (
          <div className="mt-3">
            <div className="h-1.5 w-full overflow-hidden rounded bg-zinc-200">
              <div className="h-full w-full animate-pulse rounded bg-[#001166]" />
            </div>
            <p className="mt-2 text-xs text-zinc-600">{busyMessage}</p>
          </div>
        )}
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel} disabled={controlsDisabled}>
            {cancelLabel}
          </Button>
          <Button
            type="button"
            onClick={onConfirm}
            disabled={controlsDisabled}
            className="bg-[#001166] text-white hover:bg-[#00104d]"
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
