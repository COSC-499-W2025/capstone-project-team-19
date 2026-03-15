import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

const appButtonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "bg-primary text-primary-foreground shadow-sm hover:opacity-95",
        secondary:
          "border border-border bg-secondary text-secondary-foreground hover:bg-secondary/80",
        outline:
          "border border-primary bg-background text-primary hover:bg-primary/5",
        destructive:
          "border border-destructive/20 bg-background text-destructive hover:bg-destructive/5",
        ghost: "bg-transparent text-foreground hover:bg-muted",
        icon: "bg-transparent text-foreground hover:bg-muted",
      },
      size: {
        sm: "h-9 px-3",
        default: "h-10 px-4",
        lg: "h-11 px-5",
        icon: "h-10 w-10 p-0",
      },
      fullWidth: {
        true: "w-full",
        false: "",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
      fullWidth: false,
    },
  }
);

type Props = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof appButtonVariants>;

export default function AppButton({
  className,
  variant,
  size,
  fullWidth,
  type = "button",
  ...props
}: Props) {
  return (
    <button
      type={type}
      className={cn(appButtonVariants({ variant, size, fullWidth }), className)}
      {...props}
    />
  );
}