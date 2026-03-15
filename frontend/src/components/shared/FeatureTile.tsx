import type { LucideIcon } from "lucide-react";

type Props = {
  title: string;
  icon: LucideIcon;
  onClick?: () => void;
};

export default function FeatureTile({ title, icon: Icon, onClick }: Props) {
  return (
    <button
      onClick={onClick}
      className="sectionSurface flex h-[240px] w-[280px] flex-col items-center justify-center gap-4 bg-white transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex h-24 w-24 items-center justify-center rounded-2xl bg-muted">
        <Icon className="h-10 w-10 text-primary" />
      </div>
      <span className="text-base font-medium text-foreground">{title}</span>
    </button>
  );
}