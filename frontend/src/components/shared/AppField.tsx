import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

type Props = {
  label?: string;
  helperText?: string;
  errorText?: string;
  className?: string;
  children: ReactNode;
};

export default function AppField({
  label,
  helperText,
  errorText,
  className,
  children,
}: Props) {
  return (
    <div className={cn("flex w-full flex-col gap-[6px]", className)}>
      {label ? (
        <label className="text-[14px] font-medium leading-none text-foreground">
          {label}
        </label>
      ) : null}

      {children}

      {errorText ? (
        <p className="text-[13px] leading-[1.3] text-[#cc4b4b]">{errorText}</p>
      ) : helperText ? (
        <p className="text-[13px] leading-[1.3] text-muted-foreground">
          {helperText}
        </p>
      ) : null}
    </div>
  );
}