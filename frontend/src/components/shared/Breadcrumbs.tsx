import { Link } from "react-router-dom";
import { ChevronRight } from "../../lib/ui-icons";

type BreadcrumbItem = {
  label: string;
  href?: string;
};

type Props = {
  items: BreadcrumbItem[];
};

export default function Breadcrumbs({ items }: Props) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-[4px] text-[10px] text-[#7f7f7f]">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <div key={`${item.label}-${index}`} className="flex items-center gap-[4px]">
            {item.href && !isLast ? (
              <Link to={item.href} className="hover:no-underline hover:text-foreground">
                {item.label}
              </Link>
            ) : (
              <span>{item.label}</span>
            )}

            {!isLast ? <ChevronRight className="h-[10px] w-[10px]" strokeWidth={1.5} /> : null}
          </div>
        );
      })}
    </nav>
  );
}