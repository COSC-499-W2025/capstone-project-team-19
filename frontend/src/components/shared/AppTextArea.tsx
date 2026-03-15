import type { TextareaHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = TextareaHTMLAttributes<HTMLTextAreaElement>;

export default function AppTextarea({ className, ...props }: Props) {
  return (
    <textarea
      className={cn(
        "ui-field-radius min-h-[86px] w-full resize-y border border-[#cfd5df] bg-white px-[6px] py-[6px] text-[10px] text-foreground outline-none",
        "placeholder:text-[#9aa3b2]",
        "focus:border-primary",
        className
      )}
      {...props}
    />
  );
}