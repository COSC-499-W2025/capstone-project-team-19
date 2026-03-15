import type { HTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = HTMLAttributes<HTMLElement>;

export default function PageContainer({ className, ...props }: Props) {
  return (
    <main
      className={cn("mx-auto w-full max-w-[1200px] px-6 py-8", className)}
      {...props}
    />
  );
}