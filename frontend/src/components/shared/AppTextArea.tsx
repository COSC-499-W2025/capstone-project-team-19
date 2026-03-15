import type { TextareaHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = TextareaHTMLAttributes<HTMLTextAreaElement>;

export default function AppTextarea({ className, ...props }: Props) {
  return (
    <textarea
      className={cn(
        "flex min-h-[112px] w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground shadow-sm outline-none transition",
        "placeholder:text-muted-foreground",
        "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}