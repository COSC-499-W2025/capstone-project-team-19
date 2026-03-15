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
    <div className={cn("flex w-full flex-col gap-2", className)}>
      {label ? (
        <label className="text-sm font-medium text-foreground">{label}</label>
      ) : null}

      {children}

      {errorText ? (
        <p className="text-xs text-destructive">{errorText}</p>
      ) : helperText ? (
        <p className="text-xs text-muted-foreground">{helperText}</p>
      ) : null}
    </div>
  );
}