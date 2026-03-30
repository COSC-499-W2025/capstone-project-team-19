import type { ButtonHTMLAttributes } from "react";
import type { LucideIcon } from "lucide-react";
import { Star } from "lucide-react";
import { cn } from "../../lib/utils";

/** Rank pills: brand navy, mid blue, lighter blue (matches public header #001166) */
const FEATURED_RANK_BADGE: Record<1 | 2 | 3, string> = {
  1: "bg-[#001166] text-white shadow-sm",
  2: "bg-[#1d4ed8] text-white shadow-sm",
  3: "bg-[#3b82f6] text-white shadow-sm",
};

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  title: string;
  icon?: LucideIcon;
  thumbnailUrl?: string | null;
  /** When set, shows a top-rank star badge on the thumbnail (public portfolio top projects). */
  featuredRank?: 1 | 2 | 3;
};

export default function FeatureTile({
  title,
  icon: Icon,
  thumbnailUrl,
  featuredRank,
  className,
  ...props
}: Props) {
  return (
    <button
      className={cn("w-[220px] cursor-pointer bg-transparent text-left", className)}
      {...props}
    >
      <div className="ui-surface-radius overflow-hidden border border-[#e5e5e5] bg-white">
        <div className="relative h-[120px] bg-[#efefef]">
          {featuredRank ? (
            <span
              className={cn(
                "pointer-events-none absolute left-2 top-2 z-10 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums",
                FEATURED_RANK_BADGE[featuredRank],
              )}
              aria-hidden
            >
              <Star className="h-3.5 w-3.5 fill-current" strokeWidth={0} />
              {featuredRank}
            </span>
          ) : null}
          {thumbnailUrl ? (
            <img
              src={thumbnailUrl}
              alt={title}
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
