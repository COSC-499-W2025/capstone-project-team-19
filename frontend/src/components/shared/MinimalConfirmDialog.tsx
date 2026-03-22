import { useEffect } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  message: string;
  confirmLabel?: string;
  confirmClassName?: string;
  onConfirm: () => void;
};

export default function MinimalConfirmDialog({
  open,
  onOpenChange,
  message,
  confirmLabel = "Confirm",
  confirmClassName,
  onConfirm,
}: Props) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onOpenChange(false);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onOpenChange]);

  if (!open || typeof document === "undefined") return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-black/35 p-4"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="mb-6 text-center text-[15px] leading-snug text-slate-700">
          {message}
        </p>
        <div className="flex justify-center gap-3">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            className={cn(confirmClassName)}
            onClick={() => {
              onConfirm();
              onOpenChange(false);
            }}
            data-testid="minimal-confirm-button"
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
