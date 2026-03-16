import type { TextareaHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = TextareaHTMLAttributes<HTMLTextAreaElement>;

export default function AppTextarea({ className, ...props }: Props) {
  return (
    <textarea
      className={cn(
        "ui-field-radius min-h-[110px] w-full resize-y border border-[#cfd5df] bg-white px-[8px] py-[8px] text-[14px] font-normal leading-[1.35] text-foreground outline-none",
        "placeholder:text-[#9aa3b2]",
        "focus:border-primary",
        className
      )}
      {...props}
    />
  );
}