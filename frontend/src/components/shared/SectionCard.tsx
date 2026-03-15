import type { HTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = HTMLAttributes<HTMLDivElement>;

export default function SectionCard({ className, ...props }: Props) {
  return (
    <section
      className={cn(
        "rounded-xl border border-border bg-card p-6 shadow-[0_2px_10px_rgba(0,17,102,0.06)]",
        className
      )}
      {...props}
    />
  );
}