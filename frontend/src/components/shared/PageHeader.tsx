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
  titleClassName?: string;
};

export default function PageHeader({
  title,
  subtitle,
  breadcrumbs,
  actions,
  className,
  titleClassName,
}: Props) {
  return (
    <div className={cn("flex flex-col gap-[10px]", className)}>
      {breadcrumbs?.length ? <Breadcrumbs items={breadcrumbs} /> : null}

      <div className="flex items-start justify-between gap-[12px]">
        <div className="space-y-[2px]">
          <h1 className={cn("text-[16px] font-normal text-foreground", titleClassName)}>
            {title}
          </h1>
          {subtitle ? (
            <p className="text-[10px] text-[#7f7f7f]">{subtitle}</p>
          ) : null}
        </div>

        {actions ? <div className="shrink-0">{actions}</div> : null}
      </div>
    </div>
  );
}