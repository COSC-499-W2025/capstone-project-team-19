import type { HTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Props = HTMLAttributes<HTMLElement>;

export default function PageContainer({ className, ...props }: Props) {
  return (
    <main
      className={cn("flex w-full flex-col px-[40px] py-[20px]", className)}
      {...props}
    />
  );
}