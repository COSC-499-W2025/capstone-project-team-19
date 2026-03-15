import type { HTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = HTMLAttributes<HTMLSpanElement>;

export default function TagPill({ className, ...props }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-[#d6d6d6] bg-white px-[8px] py-[2px] text-[9px] font-normal text-[#6e6e6e]",
        className
      )}
      {...props}
    />
  );
}