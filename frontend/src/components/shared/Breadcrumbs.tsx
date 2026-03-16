import { Link } from "react-router-dom";

type BreadcrumbItem = {
  label: string;
  href?: string;
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

        return (
          <div
            key={`${item.label}-${index}`}
            className="flex items-center gap-[6px]"
          >
            {item.href && !isLast ? (
              <Link
                to={item.href}
                className="hover:no-underline hover:text-foreground"
              >
                {item.label}
              </Link>
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