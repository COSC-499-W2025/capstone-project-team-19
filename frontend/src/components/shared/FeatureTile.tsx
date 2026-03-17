import type { ButtonHTMLAttributes } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  title: string;
  icon?: LucideIcon;
  thumbnailUrl?: string | null;
};

export default function FeatureTile({
  title,
  icon: Icon,
  thumbnailUrl,
  className,
  ...props
}: Props) {
  return (
    <button
      className={cn("w-[220px] bg-transparent text-left", className)}
      {...props}
    >
      <div className="ui-surface-radius overflow-hidden border border-[#e5e5e5] bg-white">
        <div className="h-[120px] bg-[#efefef]">
          {thumbnailUrl ? (
            <img
              src={thumbnailUrl}
              alt=""
              className="h-full w-full object-cover"
            />
          ) : Icon ? (
            <div className="flex h-full items-center justify-center">
              <Icon className="h-[30px] w-[30px] text-[#8e8e8e]" strokeWidth={1.6} />
            </div>
          ) : null}
        </div>

        <div className="flex h-[48px] items-center border-t border-[#ececec] px-[14px] text-[16px] font-normal leading-none text-[#3a3a3a]">
          {title}
        </div>
      </div>
    </button>
  );
}
