import { useEffect } from "react";
import { createPortal } from "react-dom";
import { X } from "../../lib/ui-icons";
import { cn } from "../../lib/utils";

type DialogWidth = "sm" | "md" | "lg";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  width?: DialogWidth;
  closeOnOverlayClick?: boolean;
  bodyClassName?: string;
};

const widthMap: Record<DialogWidth, string> = {
  sm: "max-w-[340px]",
  md: "max-w-[420px]",
  lg: "max-w-[520px]",
};

export default function AppDialogShell({
  open,
  onOpenChange,
  title,
  children,
  footer,
  width = "md",
  closeOnOverlayClick = true,
  bodyClassName,
}: Props) {
  useEffect(() => {
    if (!open) return;

    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onOpenChange(false);
    };

    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onOpenChange]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-black/35 p-4"
      onClick={() => {
        if (closeOnOverlayClick) onOpenChange(false);
      }}
    >
      <div
        className={cn(
          "ui-surface-radius ui-card-shadow w-full border border-[#dcdcdc] bg-white",
          widthMap[width]
        )}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-[#ececec] px-[10px] py-[8px]">
          <h2 className="text-[12px] font-normal text-foreground">{title}</h2>

          <button
            type="button"
            className="inline-flex h-[18px] w-[18px] items-center justify-center bg-transparent text-[#9b9b9b]"
            onClick={() => onOpenChange(false)}
            aria-label="Close dialog"
          >
            <X className="h-[12px] w-[12px]" strokeWidth={1.5} />
          </button>
        </div>

        <div className={cn("flex flex-col gap-[10px] px-[18px] py-[14px]", bodyClassName)}>
          {children}
        </div>

        {footer ? (
          <div className="flex items-center justify-end gap-[8px] border-t border-[#ececec] px-[12px] py-[8px]">
            {footer}
          </div>
        ) : null}
      </div>
    </div>,
    document.body
  );
}