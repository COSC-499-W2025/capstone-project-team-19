import { useState } from "react";
import InsightsSidebar, { type InsightsView, getPageTitle } from "./InsightsSidebar";
import { InsightsHeaderActionsProvider, useInsightsHeaderActions } from "./InsightsHeaderActionsContext";
import RankedProjectsTab from "./tabs/RankedProjectsTab";
import SkillTimelineTab from "./tabs/Skills/SkillTimelineTab";
import ChronologicalSkillsTab from "./tabs/ChronologicalSkillsTab";
import ActivityHeatmapTab from "./tabs/ActivityHeatmapTab";

export type { InsightsView };

function TitleRow({ activeView }: { activeView: InsightsView }) {
    const ctx = useInsightsHeaderActions();
    return (
        <div className="flex items-center w-full gap-4 border-b border-slate-200 pt-10 pb-2 px-6">
            <h3 className="text-lg font-semibold m-0 shrink-0">{getPageTitle(activeView)}</h3>
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
                        {activeView === "chronological-skills" && <ChronologicalSkillsTab />}
                        {activeView === "activity-heatmap" && <ActivityHeatmapTab />}
                    </main>
                </div>
            </div>
        </InsightsHeaderActionsProvider>
    );
}
