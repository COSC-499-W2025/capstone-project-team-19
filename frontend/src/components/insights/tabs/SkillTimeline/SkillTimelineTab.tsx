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
            } catch (e: unknown) {
                if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load skill timeline");
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => { cancelled = true; };
    }, []);

    if (loading) return <div className="py-4 text-center text-slate-600">Loading skill timeline...</div>;
    if (error) return <div className="py-4 text-center text-red-600">{error}</div>;
    if (!timeline) return <div className="py-4 text-center text-slate-600">No skill data available.</div>;

    return (
        <div className="flex flex-col w-full pt-2">
            <header className="relative flex items-center justify-center bg-sky-100 py-3 px-4 text-xl text-slate-800">
                <p className="m-0 text-center">
                    <span>{timeline.summary.total_skills} Skills</span>
                    <span className="mx-4 opacity-90">·</span>
                    <span>{timeline.summary.total_projects} Projects</span>
                    {timeline.summary.date_range?.earliest && timeline.summary.date_range?.latest && (
                        <>
                            <span className="mx-4 opacity-90">·</span>
                            <span>{toYMD(timeline.summary.date_range.earliest)} – {toYMD(timeline.summary.date_range.latest)}</span>
                        </>
                    )}
                </p>
                <ScoreInfoTooltip />
            </header>

            <main className="flex-1 min-w-0 px-6 mt-6">
                {activeSection === "timeline" && <DatedTimelinePanel timeline={timeline} />}
                {activeSection === "totals" && <TotalsPanel timeline={timeline} />}
                {activeSection === "undated" && <UndatedPanel events={timeline.undated} />}
            </main>
        </div>
    );
}
