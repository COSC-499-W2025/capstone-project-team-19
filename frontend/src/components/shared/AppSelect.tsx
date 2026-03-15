import type { SelectHTMLAttributes } from "react";
import { ChevronDown } from "../../lib/ui-icons";
import { cn } from "../../lib/utils";

type Props = SelectHTMLAttributes<HTMLSelectElement>;

export default function AppSelect({ className, children, ...props }: Props) {
  return (
    <div className="relative w-full">
      <select
        className={cn(
          "ui-field-radius h-[22px] w-full appearance-none border border-[#cfd5df] bg-white px-[6px] pr-[20px] text-[10px] text-foreground outline-none",
          "focus:border-primary",
          className
        )}
        {...props}
      >
        {children}
      </select>

      <ChevronDown className="pointer-events-none absolute right-[6px] top-1/2 h-[12px] w-[12px] -translate-y-1/2 text-[#7c8798]" strokeWidth={1.5} />
    </div>
  );
}