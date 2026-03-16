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
      className={cn("w-[220px] bg-transparent text-left", className)}
      {...props}
    >
      <div className="ui-surface-radius overflow-hidden border border-[#e5e5e5] bg-white">
        <div className="flex h-[120px] items-center justify-center bg-[#efefef]">
          <Icon className="h-[30px] w-[30px] text-[#8e8e8e]" strokeWidth={1.6} />
        </div>

        <div className="flex h-[48px] items-center border-t border-[#ececec] px-[14px] text-[16px] font-normal leading-none text-[#3a3a3a]">
          {title}
        </div>
      </div>
    </button>
  );
}