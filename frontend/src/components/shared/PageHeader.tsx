import type { ReactNode } from "react";
import { cn } from "../../lib/utils";
import Breadcrumbs from "./Breadcrumbs";

type BreadcrumbItem = {
  label: string;
  href?: string;
};

type Props = {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: ReactNode;
  className?: string;
};

export default function PageHeader({
  title,
  subtitle,
  breadcrumbs,
  actions,
  className,
}: Props) {
  return (
    <div className={cn("flex flex-col gap-4", className)}>
      {breadcrumbs?.length ? <Breadcrumbs items={breadcrumbs} /> : null}

      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="space-y-1">
          <h1 className="text-[32px] font-bold leading-tight text-foreground">
            {title}
          </h1>
          {subtitle ? (
            <p className="text-sm text-muted-foreground">{subtitle}</p>
          ) : null}
        </div>

        {actions ? <div className="shrink-0">{actions}</div> : null}
      </div>
    </div>
  );
}