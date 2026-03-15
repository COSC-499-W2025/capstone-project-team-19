import type { SelectHTMLAttributes } from "react";
import { ChevronDown } from "../../lib/ui-icons.ts";
import { cn } from "../../lib/utils";

type Props = SelectHTMLAttributes<HTMLSelectElement>;

export default function AppSelect({ className, children, ...props }: Props) {
  return (
    <div className="relative w-full">
      <select
        className={cn(
          "flex h-10 w-full appearance-none rounded-lg border border-input bg-background px-3 pr-10 text-sm text-foreground shadow-sm outline-none transition",
          "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        {...props}
      >
        {children}
      </select>

      <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
    </div>
  );
}