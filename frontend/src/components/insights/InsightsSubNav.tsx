export default function InsightsSubNav({ activeTab, onChange }: any) {

    const tabStyle = (tab: string) =>
        `px-4 py-3 border-2 text-sm cursor-pointer transition
        ${activeTab === tab
            ? "bg-white border-blue-600 text-black -mb-[2px]"
            : "bg-black text-white border-black hover:bg-white hover:text-black hover:border-[#b9adad]"}`;

    return (
        <div className="flex gap-2">
            <button className={tabStyle("ranked-projects")} onClick={() => onChange("ranked-projects")}>
                Ranked Projects
            </button>

            <button className={tabStyle("skill-timeline")} onClick={() => onChange("skill-timeline")}>
                Skill Timeline
            </button>

            <button className={tabStyle("chronological-skills")} onClick={() => onChange("chronological-skills")}>
                Chronological Skills
            </button>

            <button className={tabStyle("activity-heatmap")} onClick={() => onChange("activity-heatmap")}>
                Activity Heatmap
            </button>
        </div>
    );
}