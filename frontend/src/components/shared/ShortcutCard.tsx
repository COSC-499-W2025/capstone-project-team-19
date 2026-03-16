import type { ButtonHTMLAttributes } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  title: string;
  description: string;
  icon: LucideIcon;
  iconClassName?: string;
  iconBoxClassName?: string;
};

export default function ShortcutCard({
  title,
  description,
  icon: Icon,
  iconClassName,
  iconBoxClassName,
  className,
  ...props
}: Props) {
  return (
    <button
      type="button"
      className={cn(
        "ui-surface-radius flex min-h-[144px] w-full cursor-pointer flex-col items-start border border-[#e5e5e5] bg-white px-[18px] py-[16px] text-left transition-colors hover:bg-[#fafafa]",
        className
      )}
      {...props}
    >
      <div
        className={cn(
          "flex h-[26px] w-[26px] items-center justify-center rounded-[3px] bg-[#eef3ff]",
          iconBoxClassName
        )}
      >
        <Icon className={cn("h-[14px] w-[14px] text-[#6b8ff5]", iconClassName)} strokeWidth={1.9} />
      </div>

      <div className="mt-[10px] text-[16px] font-medium leading-[1.2] text-[#3c3c3c]">
        {title}
      </div>

      <div className="mt-[6px] text-[12px] leading-[1.45] text-[#777]">
        {description}
      </div>
    </button>
  );
}