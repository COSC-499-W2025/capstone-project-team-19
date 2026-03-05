import { useEffect, useMemo, useState } from "react";
import { getSkillTimeline } from "../../../../api/insights";
import type { SkillTimelineDTO, TimelineEventDTO } from "../../../../api/insights";
import SkillTimelineNav from "./SkillTimelineNav";
import DatedTimelinePanel from "./DatedTimelinePanel";
import TotalsPanel from "./TotalsPanel";
import UndatedPanel from "./UndatedPanel";

import "./SkillTimeline.css";

type SkillTimelineSection = "timeline" | "totals" | "undated";
type UndatedSortField = "skill_name" | "project_name" | "level" | "score";
type SortDirection = "asc" | "desc";

export default function SkillTimelineTab() {
    const [timeline, setTimeline] = useState<SkillTimelineDTO | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>("");
    const [activeSection, setActiveSection] = useState<SkillTimelineSection>("timeline");
    const [undatedSortField, setUndatedSortField] = useState<UndatedSortField>("skill_name");
    const [undatedSortDir, setUndatedSortDir] = useState<SortDirection>("asc");

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

    const sortedUndated = useMemo(() => {
        if (!timeline?.undated.length) return [];
        const arr = [...timeline.undated];
        const mult = undatedSortDir === "asc" ? 1 : -1;
        arr.sort((a: TimelineEventDTO, b: TimelineEventDTO) => {
            if (undatedSortField === "score") {
                return mult * (a.score - b.score);
            }
            const aVal = String(a[undatedSortField]).toLowerCase();
            const bVal = String(b[undatedSortField]).toLowerCase();
            return mult * aVal.localeCompare(bVal);
        });
        return arr;
    }, [timeline?.undated, undatedSortField, undatedSortDir]);

    if (loading) return <div className="skill-timeline-state">Loading skill timeline...</div>;
    if (error) return <div className="skill-timeline-state skill-timeline-error">{error}</div>;
    if (!timeline) return <div className="skill-timeline-state">No skill data available.</div>;

    return (
        <div className="skill-timeline-container">
            <header className="skill-timeline-header">
                <p>
                    {timeline.summary.total_skills} Skills · {timeline.summary.total_projects} Projects
                    {timeline.summary.date_range?.earliest && timeline.summary.date_range?.latest && (
                    <> · {timeline.summary.date_range.earliest} - {timeline.summary.date_range.latest}</>
                    )}
                </p>
            </header>

            <div className="skill-timeline-body">
                <SkillTimelineNav activeSection={activeSection} setActiveSection={setActiveSection} />

                <main className="skill-timeline-content">
                    {activeSection === "timeline" && <DatedTimelinePanel timeline={timeline} />}
                    {activeSection === "totals" && <TotalsPanel timeline={timeline} />}
                    {activeSection === "undated" && (
                    <UndatedPanel
                        events={timeline.undated}
                        sortedEvents={sortedUndated}
                        undatedSortField={undatedSortField}
                        setUndatedSortField={setUndatedSortField}
                        undatedSortDir={undatedSortDir}
                        setUndatedSortDir={setUndatedSortDir}
                    />
                    )}
                </main>
            </div>
        </div>
    )
}