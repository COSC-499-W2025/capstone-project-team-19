import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import PublicLayout from "./PublicLayout";
import { publicGetRanking, publicGetSkillsTimeline } from "../../api/public";
import type { PublicRankingItem } from "../../api/public";
import type { SkillTimelineDTO } from "../../api/insights";
import SkillsOverview from "../../components/insights/tabs/Skills/SkillsOverview";
import SkillProgressChart from "../../components/insights/tabs/Skills/SkillProgressChart";
import SkillsTimeline from "../../components/insights/tabs/Skills/SkillsTimeline";
import SkillsLog from "../../components/insights/tabs/Skills/SkillsLog";

type PublicView = "ranked-projects" | "skills-overview" | "skills-timeline" | "skills-log" | "activity-heatmap" | "project-heatmap";

const NAV_ITEMS: { id: PublicView; label: string; indent?: boolean }[] = [
    { id: "ranked-projects", label: "Ranked Projects" },
    { id: "activity-heatmap", label: "Activity Heatmap" },
    { id: "project-heatmap", label: "Project Heatmap" },
    { id: "skills-overview", label: "Skills Overview", indent: true },
    { id: "skills-timeline", label: "Skills Timeline", indent: true },
    { id: "skills-log", label: "Skills Log", indent: true },
];

const BADGE_STYLES = [
    "bg-slate-700 text-white font-black",
    "bg-slate-600 text-white font-black",
    "bg-slate-500 text-white font-black",
];

function RankBadge({ rank }: { rank: number }) {
    const idx = rank - 1;
    if (idx > 2) {
        return (
            <span className="w-7 h-7 inline-flex items-center justify-center text-sm text-slate-500 font-medium">
                {rank}
            </span>
        );
    }
    return (
        <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm shrink-0 ${BADGE_STYLES[idx]}`}>
            {rank}
        </span>
    );
}

function RankedProjectsView({ rankings }: { rankings: PublicRankingItem[] }) {
    if (rankings.length === 0) {
        return <div className="py-4 text-center text-slate-600">No ranked projects.</div>;
    }
    return (
        <section className="flex flex-col gap-3 pt-4">
            <div className="flex flex-col gap-3 w-fit">
                {rankings.map((p) => {
                    const idx = p.rank - 1;
                    const rowClass = `grid grid-cols-[2.5rem_14rem] gap-x-4 items-center rounded px-3 py-2 -mx-3 ${idx < 3 ? "bg-sky-50" : ""}`;
                    return (
                        <div key={p.project_summary_id} className={rowClass}>
                            <div className="flex justify-center">
                                <RankBadge rank={p.rank} />
                            </div>
                            <span className="text-sm font-medium truncate">{p.project_name}</span>
                        </div>
                    );
                })}
            </div>
        </section>
    );
}

function HeatmapPlaceholder({ title }: { title: string }) {
    return (
        <div className="py-12 flex flex-col items-center gap-2 text-slate-500">
            <p className="text-base font-medium">{title}</p>
            <p className="text-sm">Heatmap data is not available on public portfolios.</p>
        </div>
    );
}

export default function PublicInsightsPage() {
    const { username } = useParams<{ username: string }>();
    const [activeView, setActiveView] = useState<PublicView>("ranked-projects");

    const [rankings, setRankings] = useState<PublicRankingItem[]>([]);
    const [timeline, setTimeline] = useState<SkillTimelineDTO | null>(null);
    const [loadingRankings, setLoadingRankings] = useState(true);
    const [loadingTimeline, setLoadingTimeline] = useState(true);
    const [rankingsError, setRankingsError] = useState<string | null>(null);
    const [timelineError, setTimelineError] = useState<string | null>(null);

    useEffect(() => {
        if (!username) return;
        publicGetRanking(username)
            .then(setRankings)
            .catch((e: Error) => setRankingsError(e.message))
            .finally(() => setLoadingRankings(false));
        publicGetSkillsTimeline(username)
            .then(setTimeline)
            .catch((e: Error) => setTimelineError(e.message))
            .finally(() => setLoadingTimeline(false));
    }, [username]);

    const linkStyle = (id: PublicView) => {
        const active = activeView === id;
        const indent = NAV_ITEMS.find((n) => n.id === id)?.indent;
        const base = "w-full text-left py-2 px-3 text-sm cursor-pointer transition border-l-2";
        const indentClass = indent ? "pl-6" : "";
        const stateClass = active
            ? "bg-sky-50 border-l-sky-600 font-semibold text-sky-900"
            : "border-l-transparent text-slate-600 hover:bg-sky-50/50 hover:text-slate-800";
        return `${base} ${indentClass} ${stateClass}`;
    };

    function renderContent() {
        if (activeView === "ranked-projects") {
            if (loadingRankings) return <div className="py-4 text-center text-slate-600">Loading...</div>;
            if (rankingsError) return <div className="py-4 text-center text-red-600">{rankingsError}</div>;
            return <RankedProjectsView rankings={rankings} />;
        }
        if (activeView === "activity-heatmap") return <HeatmapPlaceholder title="Activity Heatmap" />;
        if (activeView === "project-heatmap") return <HeatmapPlaceholder title="Project Heatmap" />;

        if (loadingTimeline) return <div className="py-4 text-center text-slate-600">Loading...</div>;
        if (timelineError) return <div className="py-4 text-center text-red-600">{timelineError}</div>;
        if (!timeline) return <div className="py-4 text-center text-slate-600">No skill data available.</div>;

        if (activeView === "skills-overview") return <SkillsOverview timeline={timeline} />;
        if (activeView === "skills-log") return <SkillsLog timeline={timeline} />;
        if (activeView === "skills-timeline") return (
            <>
                <SkillProgressChart timeline={timeline} />
                <SkillsTimeline timeline={timeline} />
            </>
        );
    }

    const pageTitle = NAV_ITEMS.find((n) => n.id === activeView)?.label ?? "Insights";

    return (
        <PublicLayout>
            <div
                className="grid grid-cols-[12rem_1fr] grid-rows-[auto_1fr] min-h-0 flex-1 pl-4"
                style={{ minHeight: "calc(100vh - 3.5rem)" }}
            >
                {/* Row 1: aligned headers */}
                <div className="flex flex-col border-r border-slate-200 pt-10 pb-2 border-b border-slate-200">
                    <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-500 m-0 px-4">Insights</h2>
                </div>
                <div className="flex items-baseline gap-3 border-b border-slate-200 pt-10 pb-2 px-6">
                    <h3 className="text-lg font-semibold m-0">{pageTitle}</h3>
                </div>

                {/* Row 2: sidebar nav + content */}
                <nav className="flex flex-col flex-1 min-h-0 pt-2 pb-6 border-r border-slate-200 pl-4 pr-2">
                    <button className={linkStyle("ranked-projects")} onClick={() => setActiveView("ranked-projects")}>
                        Ranked Projects
                    </button>
                    <button className={linkStyle("activity-heatmap")} onClick={() => setActiveView("activity-heatmap")}>
                        Activity Heatmap
                    </button>
                    <button className={linkStyle("project-heatmap")} onClick={() => setActiveView("project-heatmap")}>
                        Project Heatmap
                    </button>
                    <div className="pt-4 mt-2 border-t border-slate-200 text-[11px] font-medium text-slate-500 uppercase tracking-widest px-3 pb-1.5 select-none">
                        Skills
                    </div>
                    <button className={linkStyle("skills-overview")} onClick={() => setActiveView("skills-overview")}>
                        Skills Overview
                    </button>
                    <button className={linkStyle("skills-timeline")} onClick={() => setActiveView("skills-timeline")}>
                        Skills Timeline
                    </button>
                    <button className={linkStyle("skills-log")} onClick={() => setActiveView("skills-log")}>
                        Skills Log
                    </button>
                </nav>
                <div className="flex flex-col min-w-0 px-6 pb-6 overflow-auto">
                    <main className="flex-1 min-h-0">
                        {renderContent()}
                    </main>
                </div>
            </div>
        </PublicLayout>
    );
}
