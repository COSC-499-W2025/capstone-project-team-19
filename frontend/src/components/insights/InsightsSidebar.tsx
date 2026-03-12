export type InsightsView = "ranked-projects" | "skill-timeline-timeline" | "skill-timeline-totals" | "skill-timeline-undated" | "chronological-skills" | "activity-heatmap";

const NAV_ITEMS: { id: InsightsView; label: string; indent?: boolean }[] = [
    { id: "ranked-projects", label: "Ranked Projects" },
    { id: "skill-timeline-timeline", label: "Timeline", indent: true },
    { id: "skill-timeline-totals", label: "Current Totals", indent: true },
    { id: "skill-timeline-undated", label: "Undated Skills", indent: true },
    { id: "chronological-skills", label: "Chronological Skills" },
    { id: "activity-heatmap", label: "Activity Heatmap" },
];

export function getPageTitle(view: InsightsView): string {
    return NAV_ITEMS.find((n) => n.id === view)?.label ?? view;
}

export default function InsightsSidebar({ activeView, onChange, hideHeader }: { activeView: InsightsView; onChange: (view: InsightsView) => void; hideHeader?: boolean; }) {
    const linkStyle = (id: InsightsView) => {
        const active = activeView === id;
        const base = "w-full text-left py-2 px-3 text-sm cursor-pointer transition border-l-2";
        const activeClasses = "bg-sky-50 border-l-sky-600 font-semibold text-sky-900";
        const inactiveClasses = "border-l-transparent text-slate-600 hover:bg-sky-50/50 hover:text-slate-800";
        const indentClasses = id && NAV_ITEMS.find((n) => n.id === id)?.indent ? "pl-6" : "";

        return `${base} ${indentClasses} ${active ? activeClasses : inactiveClasses}`;
    };

    const navContent = (
        <nav className={`flex flex-col flex-1 min-h-0 pt-2 pb-6 ${hideHeader ? "border-r border-slate-200 pl-4 pr-2" : ""}`}>
            <button className={linkStyle("ranked-projects")} onClick={() => onChange("ranked-projects")}>{NAV_ITEMS.find((n) => n.id === "ranked-projects")!.label}</button>
            <div className="pt-4 mt-2 border-t border-slate-200 text-[11px] font-medium text-slate-500 uppercase tracking-widest px-3 pb-1.5 select-none">Skill Timeline</div>
            {NAV_ITEMS.filter((n) => n.indent).map((n) => (
                <button key={n.id} className={linkStyle(n.id)} onClick={() => onChange(n.id)}>{n.label}</button>
            ))}
            <div className="border-t border-slate-200 mt-2 pt-2" />
            <button className={linkStyle("chronological-skills")} onClick={() => onChange("chronological-skills")}>{NAV_ITEMS.find((n) => n.id === "chronological-skills")!.label}</button>
            <div className="border-t border-slate-200 mt-2 pt-2" />
            <button className={linkStyle("activity-heatmap")} onClick={() => onChange("activity-heatmap")}>{NAV_ITEMS.find((n) => n.id === "activity-heatmap")!.label}</button>
        </nav>
    );

    if (hideHeader) return navContent;
    return (
        <>
            <div className="flex items-center border-b border-slate-200 py-3 -mx-2 px-4">
                <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-500 m-0">Insights</h2>
            </div>
            {navContent}
        </>
    );
}
