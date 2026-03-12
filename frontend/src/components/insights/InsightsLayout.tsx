import { useState } from "react";
import InsightsSidebar, { type InsightsView } from "./InsightsSidebar";
import RankedProjectsTab from "./tabs/RankedProjectsTab";
import SkillTimelineTab from "./tabs/SkillTimeline/SkillTimelineTab";
import ChronologicalSkillsTab from "./tabs/ChronologicalSkillsTab";
import ActivityHeatmapTab from "./tabs/ActivityHeatmapTab";

export type { InsightsView };

export default function InsightsLayout() {
    const [activeView, setActiveView] = useState<InsightsView>("ranked-projects");

    const isSkillTimeline = activeView.startsWith("skill-timeline-");
    const skillTimelineSection = isSkillTimeline
        ? (activeView.replace("skill-timeline-", "") as "timeline" | "totals" | "undated")
        : "timeline";

    return (
        <div className="flex min-h-0 flex-1 pl-4">
            <InsightsSidebar activeView={activeView} onChange={setActiveView} />

            <div className="flex-1 min-w-0 flex flex-col px-6 pb-6 pt-10">
                <main className="flex-1 min-h-0">
                    {activeView === "ranked-projects" && <RankedProjectsTab />}
                    {isSkillTimeline && (
                        <SkillTimelineTab activeSection={skillTimelineSection} />
                    )}
                    {activeView === "chronological-skills" && <ChronologicalSkillsTab />}
                    {activeView === "activity-heatmap" && <ActivityHeatmapTab />}
                </main>
            </div>
        </div>
    );
}
