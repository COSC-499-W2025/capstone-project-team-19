import { useState } from "react";
import InsightsSubNav from "./InsightsSubNav";
import RankedProjectsTab from "./tabs/RankedProjectsTab";
import SkillTimelineTab from "./tabs/SkillTimelineTab";
import ChronologicalSkillsTab from "./tabs/ChronologicalSkillsTab";
import ActivityHeatmapTab from "./tabs/ActivityHeatmapTab";

export default function InsightsLayout() {
    const [activeTab, setActiveTab] = useState("ranked-projects");

    return (
        <div className="insights-container">
            <h2>Insights</h2>

            <InsightsSubNav activeTab={activeTab} onChange={setActiveTab} />
            
            <div className="insights-nav">
                {activeTab === "ranked-projects" && <RankedProjectsTab />}
                {activeTab === "skill-timeline" && <SkillTimelineTab />}
                {activeTab === "chronological-skills" && <ChronologicalSkillsTab />}
                {activeTab === "activity-heatmap" && <ActivityHeatmapTab />}
            </div>
        </div>
    );
}