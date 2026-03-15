import { cn } from "../../lib/utils";

type Tab = {
  key: string;
  label: string;
};

type Props = {
  tabs: Tab[];
  activeKey: string;
  onChange: (key: string) => void;
  align?: "left" | "right";
};

export default function SectionTabs({
  tabs,
  activeKey,
  onChange,
  align = "right",
}: Props) {
  return (
    <div className={cn("flex border-b border-[#e6e6e6]", align === "right" && "justify-end")}>
      {tabs.map((tab) => {
        const active = tab.key === activeKey;

        return (
          <button
            key={tab.key}
            type="button"
            onClick={() => onChange(tab.key)}
            className={cn(
              "relative h-[24px] px-[10px] text-[10px] text-[#666]",
              active && "text-foreground"
            )}
          >
            {tab.label}
            {active ? (
              <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-primary" />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}