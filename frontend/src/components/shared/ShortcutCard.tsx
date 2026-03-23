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
        "ui-surface-radius flex h-[128px] w-full cursor-pointer items-start gap-[15px] border border-[#E5E5E5] bg-white px-[21px] py-[21px] text-left transition-colors hover:bg-[#fafafa]",
        className
      )}
      {...props}
    >
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-[3px] bg-[#EAF2FF]",
          iconBoxClassName
        )}
      >
        <Icon
          className={cn("h-6 w-6 text-[#69A2F8]", iconClassName)}
          strokeWidth={2.3}
        />
      </div>

      <div className="w-[240px] pt-[7px]">
        <div className="text-[16px] font-medium leading-5 text-[#2F2F2F]">
          {title}
        </div>

        <div className="mt-[3px] text-[12px] font-normal leading-5 text-[#6C6C6C]">
          {description}
        </div>
      </div>
    </button>
  );
}