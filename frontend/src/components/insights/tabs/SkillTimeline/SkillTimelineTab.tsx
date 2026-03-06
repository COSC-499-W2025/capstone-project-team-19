import { useEffect, useState } from "react";
import { getSkillTimeline } from "../../../../api/insights";
import type { SkillTimelineDTO } from "../../../../api/insights";
import SkillTimelineNav from "./SkillTimelineNav";
import DatedTimelinePanel from "./DatedTimelinePanel";
import TotalsPanel from "./TotalsPanel";
import UndatedPanel from "./UndatedPanel";
import { toYMD } from "./formatHelpers";

import "./SkillTimeline.css";

type SkillTimelineSection = "timeline" | "totals" | "undated";

export default function SkillTimelineTab() {
    const [timeline, setTimeline] = useState<SkillTimelineDTO | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>("");
    const [activeSection, setActiveSection] = useState<SkillTimelineSection>("timeline");

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

    if (loading) return <div className="skill-timeline-state">Loading skill timeline...</div>;
    if (error) return <div className="skill-timeline-state skill-timeline-error">{error}</div>;
    if (!timeline) return <div className="skill-timeline-state">No skill data available.</div>;

    return (
        <div className="skill-timeline-container">
            <header className="skill-timeline-header">
                <p>
                    {timeline.summary.total_skills} Skills · {timeline.summary.total_projects} Projects
                    {timeline.summary.date_range?.earliest && timeline.summary.date_range?.latest && (
                    <> · {toYMD(timeline.summary.date_range.earliest)} - {toYMD(timeline.summary.date_range.latest)}</>
                    )}
                </p>
            </header>

            <div className="skill-timeline-body">
                <SkillTimelineNav activeSection={activeSection} setActiveSection={setActiveSection} />

                <main className="skill-timeline-content">
                    {activeSection === "timeline" && <DatedTimelinePanel timeline={timeline} />}
                    {activeSection === "totals" && <TotalsPanel timeline={timeline} />}
                    {activeSection === "undated" && <UndatedPanel events={timeline.undated} />}
                </main>
            </div>
        </div>
    )
}