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
    <div className={cn("flex w-full flex-col gap-[4px]", className)}>
      {label ? (
        <label className="text-[10px] font-medium text-foreground">{label}</label>
      ) : null}

      {children}

      {errorText ? (
        <p className="text-[10px] text-[#cc4b4b]">{errorText}</p>
      ) : helperText ? (
        <p className="text-[10px] text-muted-foreground">{helperText}</p>
      ) : null}
    </div>
  );
}