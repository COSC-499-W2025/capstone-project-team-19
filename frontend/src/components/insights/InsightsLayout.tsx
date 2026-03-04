import { useState } from "react";
import InsightsSubNav from "./InsightsSubNav";
import RankedProjectsTab from "./tabs/RankedProjectsTab";
import SkillTimelineTab from "./tabs/SkillTimelineTab";
import ChronologicalSkillsTab from "./tabs/ChronologicalSkillsTab";
import ActivityHeatmapTab from "./tabs/ActivityHeatmapTab";
import "../insights/Insights.css";

export default function InsightsLayout() {
    const [activeTab, setActiveTab] = useState("ranked-projects");

    return (
        <div className="insights-container">
            <header className="insights-top">
                <h2 className="insights-header">Insights</h2>
                <InsightsSubNav activeTab={activeTab} onChange={setActiveTab} />
            </header>
            
            <div className="insights-content">
                {activeTab === "ranked-projects" && <RankedProjectsTab />}
                {activeTab === "skill-timeline" && <SkillTimelineTab />}
                {activeTab === "chronological-skills" && <ChronologicalSkillsTab />}
                {activeTab === "activity-heatmap" && <ActivityHeatmapTab />}
            </div>
        </div>
    );
}