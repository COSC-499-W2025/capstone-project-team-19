import { useEffect, useState } from "react";
import { getSkillTimeline } from "../../../../api/insights";
import type { SkillTimelineDTO } from "../../../../api/insights";
import DatedTimelinePanel from "./DatedTimelinePanel";
import TotalsPanel from "./TotalsPanel";
import UndatedPanel from "./UndatedPanel";
import { toYMD } from "./utils/formatHelpers";
import ScoreInfoTooltip from "./ScoreInfoTooltip";

type SkillTimelineSection = "timeline" | "totals" | "undated";

export default function SkillTimelineTab({ activeSection }: { activeSection: SkillTimelineSection }) {
    const [timeline, setTimeline] = useState<SkillTimelineDTO | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>("");

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                setLoading(true);
                setError("");
                const res = await getSkillTimeline();
                if (res.success && res.data) {
                    if (!cancelled) setTimeline(res.data);
                }
            }
            catch (e: unknown) {
                if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load skill timeline");
            }
            finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => { cancelled = true; };
    }, []);

    if (loading) return <div className="py-4 text-center text-slate-600">Loading skill timeline...</div>;
    if (error) return <div className="py-4 text-center text-red-600">{error}</div>;
    if (!timeline) return <div className="py-4 text-center text-slate-600">No skill data available.</div>;

    const sectionTitles: Record<SkillTimelineSection, string> = {
        timeline: "Timeline",
        totals: "Current Totals",
        undated: "Undated Skills",
    };
    const dateRange =
        timeline.summary.date_range?.earliest && timeline.summary.date_range?.latest
            ? ` · ${toYMD(timeline.summary.date_range.earliest)} – ${toYMD(timeline.summary.date_range.latest)}`
            : "";

    return (
        <div className="flex flex-col w-full">
            <div className="relative flex justify-between items-center mb-4">
                <div>
                    <p className="text-sm text-slate-600 m-0">
                        {timeline.summary.total_skills} skills · {timeline.summary.total_projects} projects{dateRange}
                    </p>
                </div>
                <ScoreInfoTooltip />
            </div>

            <main className="flex-1 min-w-0 px-6">
                {activeSection === "timeline" && <DatedTimelinePanel timeline={timeline} />}
                {activeSection === "totals" && <TotalsPanel timeline={timeline} />}
                {activeSection === "undated" && <UndatedPanel events={timeline.undated} />}
            </main>
        </div>
    );
}
