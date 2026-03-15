import type { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Variant = "primary" | "outline" | "ghost" | "destructive";
type Size = "sm" | "default" | "lg" | "icon";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  fullWidth?: boolean;
};

const variantClasses: Record<Variant, string> = {
  primary:
    "border border-primary bg-primary text-primary-foreground hover:bg-[#00104f]",
  outline:
    "border border-primary bg-white text-primary hover:bg-[#f7f9ff]",
  ghost: "border border-transparent bg-transparent text-foreground hover:bg-muted",
  destructive:
    "border border-[#d9a5a5] bg-white text-[#cc4b4b] hover:bg-[#fff6f6]",
};

const sizeClasses: Record<Size, string> = {
  sm: "h-[22px] px-[8px] text-[10px]",
  default: "h-[26px] px-[12px] text-[11px]",
  lg: "h-[30px] px-[14px] text-[12px]",
  icon: "h-[24px] w-[24px] p-0 text-[11px]",
};

export default function AppButton({
  className,
  variant = "primary",
  size = "default",
  fullWidth = false,
  type = "button",
  ...props
}: Props) {
  return (
    <button
      type={type}
      className={cn(
        "ui-button-radius inline-flex items-center justify-center gap-1 font-medium leading-none outline-none transition disabled:pointer-events-none disabled:opacity-50",
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && "w-full",
        className
      )}
      {...props}
    />
  );
}