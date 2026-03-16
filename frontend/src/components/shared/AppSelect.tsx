import type { SelectHTMLAttributes } from "react";
import { ChevronDown } from "../../lib/ui-icons";
import { cn } from "../../lib/utils";

type Props = SelectHTMLAttributes<HTMLSelectElement>;

export default function AppSelect({ className, children, ...props }: Props) {
  return (
    <div className="relative w-full">
      <select
        className={cn(
          "ui-field-radius h-[34px] w-full appearance-none border border-[#cfd5df] bg-white px-[8px] pr-[28px] text-[14px] font-normal leading-none text-foreground outline-none",
          "focus:border-primary",
          className
        )}
        {...props}
      >
        {children}
      </select>

      <ChevronDown
        className="pointer-events-none absolute right-[8px] top-1/2 h-[14px] w-[14px] -translate-y-1/2 text-[#7c8798]"
        strokeWidth={1.5}
      />
    </div>
  );
}