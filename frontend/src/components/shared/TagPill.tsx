import type { HTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = HTMLAttributes<HTMLSpanElement>;

export default function TagPill({ className, ...props }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-[#d6d6d6] bg-white px-[10px] py-[3px] text-[14px] font-normal leading-none text-[#6e6e6e]",
        className
      )}
      {...props}
    />
  );
}