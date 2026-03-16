import type { InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label?: string;
  labelClassName?: string;
};

export default function AppRadio({
  className,
  label,
  labelClassName,
  ...props
}: Props) {
  return (
    <label className="inline-flex items-center gap-[6px]">
      <input type="radio" className={cn("peer sr-only", className)} {...props} />

      <span className="inline-block h-[12px] w-[12px] shrink-0 rounded-full border border-[#c8c8c8] bg-white peer-checked:border-primary peer-checked:bg-primary" />

      {label ? (
        <span
          className={cn(
            "text-[13px] font-normal leading-none text-[#3f3f3f]",
            labelClassName
          )}
        >
          {label}
        </span>
      ) : null}
    </label>
  );
}