import { useState } from "react";
import InsightsSidebar, { type InsightsView, getPageTitle } from "./InsightsSidebar";
import { InsightsHeaderActionsProvider, useInsightsHeaderActions } from "./InsightsHeaderActionsContext";
import RankedProjectsTab from "./tabs/Projects/RankedProjectsTab";
import SkillTimelineTab from "./tabs/Skills/SkillTimelineTab";
import SkillsLog from "./tabs/Skills/SkillsLog";
import ActivityHeatmapTab from "./tabs/Projects/ActivityHeatmapTab";
import ProjectSkillHeatmapTab from "./tabs/Projects/ProjectSkillHeatmapTab";

export type { InsightsView };

function TitleRow({ activeView }: { activeView: InsightsView }) {
    const ctx = useInsightsHeaderActions();
    return (
        <div className="flex items-center w-full gap-4 border-b border-slate-200 pt-10 pb-2 px-6">
            <div className="flex items-baseline gap-3 shrink-0 min-w-0">
                <h3 className="text-lg font-semibold m-0">{getPageTitle(activeView)}</h3>
                {activeView === "ranked-projects" && (
                    <span className="ml-3 text-sm text-slate-600">
                        Your top 3 ranked projects are displayed on your portfolio. Move projects higher if you want them featured.
                    </span>
                )}
            </div>
            <div className="flex-1 flex items-center min-w-0 gap-3">
                {ctx?.actions}
            </div>
        </div>
    );
}

export default function InsightsLayout() {
    const [activeView, setActiveView] = useState<InsightsView>("ranked-projects");

    const isSkillTimeline = activeView.startsWith("skill-timeline-");
    const skillTimelineSection = isSkillTimeline
        ? (activeView.replace("skill-timeline-", "") as "timeline" | "totals")
        : "timeline";

    return (
        <InsightsHeaderActionsProvider>
            <div className="grid grid-cols-[12rem_1fr] grid-rows-[auto_1fr] min-h-0 flex-1 pl-4">
                {/* Row 1: Headers aligned horizontally */}
                <div className="flex flex-col border-r border-slate-200 pt-10 pb-2 border-b border-slate-200">
                    <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-500 m-0 px-4">Insights</h2>
                </div>
                <TitleRow activeView={activeView} />

                {/* Row 2: Sidebar nav + content */}
                <InsightsSidebar activeView={activeView} onChange={setActiveView} hideHeader />
                <div className="flex flex-col min-w-0 px-6 pb-6 overflow-auto">
                    <main className="flex-1 min-h-0">
                        {activeView === "ranked-projects" && <RankedProjectsTab />}
                        {isSkillTimeline && (
                            <SkillTimelineTab activeSection={skillTimelineSection} />
                        )}
                        {activeView === "chronological-skills" && <SkillsLog />}
                        {activeView === "activity-heatmap" && <ActivityHeatmapTab />}
                        {activeView === "project-heatmap" && <ProjectSkillHeatmapTab />}
                    </main>
                </div>
            </div>
        </InsightsHeaderActionsProvider>
    );
}
