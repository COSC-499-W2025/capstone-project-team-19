import { useState } from "react";
import InsightsSidebar, {
  type InsightsView,
  getPageTitle,
} from "./InsightsSidebar";
import {
  InsightsHeaderActionsProvider,
  useInsightsHeaderActions,
} from "./InsightsHeaderActionsContext";
import RankedProjectsTab from "./tabs/Projects/RankedProjectsTab";
import SkillTimelineTab from "./tabs/Skills/SkillTimelineTab";
import SkillsLog from "./tabs/Skills/SkillsLog";
import ActivityHeatmapTab from "./tabs/Projects/ActivityHeatmapTab";
import ProjectSkillHeatmapTab from "./tabs/Projects/ProjectSkillHeatmapTab";

export type { InsightsView };

function TitleRow({ activeView }: { activeView: InsightsView }) {
  const ctx = useInsightsHeaderActions();

  return (
    <div className="flex w-full min-w-0 flex-wrap items-start justify-between gap-x-4 gap-y-3 border-b border-slate-200 px-6 pb-3 pt-10">
      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 flex-wrap items-baseline gap-x-3 gap-y-2">
          <h3 className="m-0 text-lg font-semibold text-slate-900">
            {getPageTitle(activeView)}
          </h3>

          {activeView === "ranked-projects" && (
            <span className="min-w-0 max-w-full text-sm leading-5 text-slate-600">
              Your top 3 ranked projects are displayed on your portfolio. Move
              projects higher if you want them featured.
            </span>
          )}
        </div>
      </div>

      {ctx?.actions ? (
        <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
          {ctx.actions}
        </div>
      ) : null}
    </div>
  );
}

export default function InsightsLayout() {
  const [activeView, setActiveView] =
    useState<InsightsView>("ranked-projects");

  const isSkillTimeline = activeView.startsWith("skill-timeline-");
  const skillTimelineSection = isSkillTimeline
    ? (activeView.replace("skill-timeline-", "") as "timeline" | "totals")
    : "timeline";

  return (
    <InsightsHeaderActionsProvider>
      <div className="grid min-h-0 flex-1 grid-cols-[180px_minmax(0,1fr)] grid-rows-[auto_1fr]">
        {/* Row 1: left header cell */}
        <div className="flex flex-col border-b border-r border-slate-200 px-6 pb-3 pt-10">
          <h2 className="m-0 text-sm font-semibold uppercase tracking-widest text-slate-500">
            Insights
          </h2>
        </div>

        {/* Row 1: title + actions */}
        <TitleRow activeView={activeView} />

        {/* Row 2: sidebar + content */}
        <InsightsSidebar
          activeView={activeView}
          onChange={setActiveView}
          hideHeader
        />

        <div className="flex min-w-0 flex-col overflow-auto px-6 pb-6">
          <main className="min-h-0 flex-1">
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