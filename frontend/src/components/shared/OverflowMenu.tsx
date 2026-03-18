import { useEffect, useRef, useState } from "react";
import { MoreVertical } from "../../lib/ui-icons";
import { cn } from "../../lib/utils";

type Item = {
  label: string;
  onClick: () => void;
  destructive?: boolean;
};

type Props = {
  items: Item[];
  className?: string;
};

export default function OverflowMenu({ items, className }: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  return (
    <div ref={rootRef} className={cn("relative inline-flex", className)}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="inline-flex h-[20px] w-[20px] items-center justify-center bg-transparent text-[#8c8c8c]"
        aria-label="Open options"
      >
        <MoreVertical className="h-[14px] w-[14px]" strokeWidth={1.5} />
      </button>

      {open ? (
        <div className="ui-surface-radius ui-menu-shadow absolute right-0 top-[22px] z-50 min-w-[170px] border border-[#dcdcdc] bg-white py-[4px]">
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => {
                item.onClick();
                setOpen(false);
              }}
              className={cn(
                "flex h-[30px] w-full items-center whitespace-nowrap px-[10px] text-left text-[12px] font-normal leading-none text-foreground hover:bg-[#f5f5f5]",
                item.destructive && "text-[#cc4b4b]"
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}