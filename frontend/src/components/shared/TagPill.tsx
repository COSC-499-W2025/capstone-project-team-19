import type { HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const tagPillVariants = cva(
  "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium",
  {
    variants: {
      variant: {
        neutral: "border-border bg-muted text-muted-foreground",
        primary: "border-primary/15 bg-primary/5 text-primary",
        success: "border-green-200 bg-green-50 text-green-700",
        warning: "border-amber-200 bg-amber-50 text-amber-700",
        destructive: "border-red-200 bg-red-50 text-red-700",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  }
);

type Props = HTMLAttributes<HTMLSpanElement> &
  VariantProps<typeof tagPillVariants>;

export default function TagPill({ className, variant, ...props }: Props) {
  return <span className={cn(tagPillVariants({ variant }), className)} {...props} />;
}