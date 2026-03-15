import type { ButtonHTMLAttributes } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  title: string;
  description?: string;
  icon: LucideIcon;
};

export default function FeatureTile({
  title,
  description,
  icon: Icon,
  className,
  ...props
}: Props) {
  return (
    <button
      className={cn(
        "flex min-h-[220px] w-full max-w-[280px] flex-col items-center justify-center gap-4 rounded-xl border border-border bg-card px-6 py-8 text-center shadow-[0_2px_10px_rgba(0,17,102,0.06)] transition hover:-translate-y-0.5 hover:shadow-[0_8px_24px_rgba(0,17,102,0.12)]",
        className
      )}
      {...props}
    >
      <div className="flex h-24 w-24 items-center justify-center rounded-2xl bg-muted">
        <Icon className="h-10 w-10 text-primary" />
      </div>

      <div className="space-y-1">
        <h3 className="text-base font-semibold text-foreground">{title}</h3>
        {description ? (
          <p className="text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
    </button>
  );
}