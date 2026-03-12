import { useState } from "react";
import InsightsSubNav from "./InsightsSubNav";
import RankedProjectsTab from "./tabs/RankedProjectsTab";
import SkillTimelineTab from "./tabs/SkillTimeline/SkillTimelineTab";
import ChronologicalSkillsTab from "./tabs/ChronologicalSkillsTab";
import ActivityHeatmapTab from "./tabs/ActivityHeatmapTab";

export default function InsightsLayout() {
    const [activeTab, setActiveTab] = useState("ranked-projects");

    return (
        <div className="px-6 pb-6 flex flex-col">
            <header className="w-full flex justify-between items-end gap-4 border-b-2 border-black p-3">
                <h2 className="text-xl font-semibold">Insights</h2>
                <InsightsSubNav activeTab={activeTab} onChange={setActiveTab} />
            </header>

            <div className="mt-3">
                {activeTab === "ranked-projects" && <RankedProjectsTab />}
                {activeTab === "skill-timeline" && <SkillTimelineTab />}
                {activeTab === "chronological-skills" && <ChronologicalSkillsTab />}
                {activeTab === "activity-heatmap" && <ActivityHeatmapTab />}
            </div>
        </div>
    );
}