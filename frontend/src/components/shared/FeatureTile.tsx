import type { ButtonHTMLAttributes } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  title: string;
  icon: LucideIcon;
};

export default function FeatureTile({
  title,
  icon: Icon,
  className,
  ...props
}: Props) {
  return (
    <button
      className={cn("w-[180px] bg-transparent text-left", className)}
      {...props}
    >
      <div className="ui-surface-radius overflow-hidden border border-[#e5e5e5] bg-white">
        <div className="flex h-[95px] items-center justify-center bg-[#efefef]">
          <Icon className="h-[24px] w-[24px] text-[#8e8e8e]" strokeWidth={1.6} />
        </div>

        <div className="flex h-[32px] items-center border-t border-[#ececec] px-[10px] text-[11px] text-[#3a3a3a]">
          {title}
        </div>
      </div>
    </button>
  );
}