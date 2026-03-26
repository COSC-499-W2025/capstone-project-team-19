import { Link } from "react-router-dom";

type BreadcrumbItem = {
  label: string;
  href?: string;
  onClick?: () => void;
};

type Props = {
  items: BreadcrumbItem[];
};

export default function Breadcrumbs({ items }: Props) {
  return (
    <nav
      aria-label="Breadcrumb"
      className="flex items-center gap-[6px] text-[16px] font-normal leading-none text-[#7f7f7f]"
    >
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        const isClickable = !isLast && (item.href || item.onClick);

        return (
          <div
            key={`${item.label}-${index}`}
            className="flex items-center gap-[6px]"
          >
            {isClickable ? (
              item.onClick ? (
                <button
                  type="button"
                  onClick={item.onClick}
                  className="text-[#7f7f7f] hover:text-foreground"
                >
                  {item.label}
                </button>
              ) : (
                <Link
                  to={item.href!}
                  className="hover:no-underline hover:text-foreground"
                >
                  {item.label}
                </Link>
              )
            ) : (
              <span>{item.label}</span>
            )}

            {!isLast ? <span className="text-[#7f7f7f]">/</span> : null}
          </div>
        );
      })}
    </nav>
  );
}