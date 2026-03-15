import type { HTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = HTMLAttributes<HTMLDivElement>;

export default function SectionCard({ className, ...props }: Props) {
  return (
    <section
      className={cn(
        "ui-surface-radius border border-[#e5e5e5] bg-white px-[14px] py-[14px]",
        className
      )}
      {...props}
    />
  );
}