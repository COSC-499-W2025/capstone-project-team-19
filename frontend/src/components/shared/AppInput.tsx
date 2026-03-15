import type { InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = InputHTMLAttributes<HTMLInputElement>;

export default function AppInput({ className, ...props }: Props) {
  return (
    <input
      className={cn(
        "ui-field-radius h-[22px] w-full border border-[#cfd5df] bg-white px-[6px] text-[10px] text-foreground outline-none",
        "placeholder:text-[#9aa3b2]",
        "focus:border-primary",
        className
      )}
      {...props}
    />
  );
}