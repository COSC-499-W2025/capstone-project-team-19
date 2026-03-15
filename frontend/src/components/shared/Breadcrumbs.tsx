import { Link } from "react-router-dom";
import { ChevronRight } from "../../lib/ui-icons.ts";

type BreadcrumbItem = {
  label: string;
  href?: string;
};

type Props = {
  items: BreadcrumbItem[];
};

export default function Breadcrumbs({ items }: Props) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-muted-foreground">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <div key={`${item.label}-${index}`} className="flex items-center gap-2">
            {item.href && !isLast ? (
              <Link to={item.href} className="hover:text-foreground hover:no-underline">
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? "text-foreground" : ""}>{item.label}</span>
            )}

            {!isLast ? <ChevronRight className="h-3.5 w-3.5" /> : null}
          </div>
        );
      })}
    </nav>
  );
}