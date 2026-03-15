import { useEffect } from "react";
import { createPortal } from "react-dom";
import { X } from "../../lib/ui-icons.ts";
import { cn } from "../../lib/utils";
import AppButton from "./AppButton";

type DialogWidth = "sm" | "md" | "lg" | "xl";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  width?: DialogWidth;
  closeOnOverlayClick?: boolean;
};

const widthMap: Record<DialogWidth, string> = {
  sm: "max-w-md",
  md: "max-w-xl",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
};

export default function AppDialogShell({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  width = "lg",
  closeOnOverlayClick = true,
}: Props) {
  useEffect(() => {
    if (!open) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onOpenChange(false);
    };

    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onOpenChange]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/35 p-4"
      onClick={() => {
        if (closeOnOverlayClick) onOpenChange(false);
      }}
    >
      <div
        className={cn(
          "w-full rounded-2xl border border-border bg-card p-6 shadow-[0_20px_40px_rgba(0,17,102,0.12)]",
          widthMap[width]
        )}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-6 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold text-foreground">{title}</h2>
            {description ? (
              <p className="text-sm text-muted-foreground">{description}</p>
            ) : null}
          </div>

          <AppButton
            variant="ghost"
            size="icon"
            aria-label="Close dialog"
            onClick={() => onOpenChange(false)}
          >
            <X className="h-5 w-5" />
          </AppButton>
        </div>

        <div className="flex flex-col gap-4">{children}</div>

        {footer ? (
          <div className="mt-6 flex items-center justify-end gap-3">{footer}</div>
        ) : null}
      </div>
    </div>,
    document.body
  );
}