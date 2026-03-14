import { useEffect, useState, useMemo } from "react";
import { getSkillTimeline } from "../../../../api/insights";
import type { SkillTimelineDTO } from "../../../../api/insights";
import { formatSkillName } from "./utils/formatHelpers";
import type { EventWithDate } from "./SkillsLogRow";
import SkillsLogRow from "./SkillsLogRow";

function matchesEvent(e: EventWithDate, search: string, projectFilter: string) {
    const q = search.trim().toLowerCase();
    const matchesSkill = q === "" || formatSkillName(e.skill_name).toLowerCase().includes(q);
    const matchesProject = projectFilter === "" || e.project_name === projectFilter;
    return matchesSkill && matchesProject;
}

export default function SkillsLog() {
    const [timeline, setTimeline] = useState<SkillTimelineDTO | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>("");
    const [search, setSearch] = useState("");
    const [projectFilter, setProjectFilter] = useState("");

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                setLoading(true);
                setError("");
                const res = await getSkillTimeline();
                if (res.success && res.data && !cancelled) setTimeline(res.data);
            } catch (e: unknown) {
                if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load skill timeline");
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => { cancelled = true; };
    }, []);

    const datedEvents = useMemo(
        () => (timeline?.dated ?? []).flatMap((g) => g.events.map((e) => ({ ...e, date: g.date }))),
        [timeline?.dated]
    );

    const projects = useMemo(() => {
        const seen = new Set<string>();
        for (const e of datedEvents) seen.add(e.project_name);
        for (const e of timeline?.undated ?? []) seen.add(e.project_name);
        return [...seen].sort();
    }, [datedEvents, timeline?.undated]);

    const filteredDated = useMemo(
        () => datedEvents.filter((e) => matchesEvent(e, search, projectFilter)),
        [datedEvents, search, projectFilter]
    );
    const filteredUndated = useMemo(
        () => (timeline?.undated ?? []).filter((e) => matchesEvent(e, search, projectFilter)),
        [timeline?.undated, search, projectFilter]
    );

    return loading ? (
        <div className="py-4 text-center text-slate-600">Loading skill timeline...</div>
    ) : error ? (
        <div className="py-4 text-center text-red-600">{error}</div>
    ) : !timeline ? (
        <div className="py-4 text-center text-slate-600">No skill data available.</div>
    ) : (
        <div className="flex flex-col gap-6 pt-4">
            <div className="flex flex-wrap items-center gap-4">
                <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search skills..."
                    className="rounded-lg border border-slate-300 px-3 py-2 text-sm w-full max-w-xs outline-none focus:border-slate-500"
                    aria-label="Search skills"
                />
                <select
                    value={projectFilter}
                    onChange={(e) => setProjectFilter(e.target.value)}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
                    aria-label="Filter by project"
                >
                    <option value="">All projects</option>
                    {projects.map((p) => (
                        <option key={p} value={p}>{p}</option>
                    ))}
                </select>
            </div>

            <section className="rounded-lg border border-slate-200 bg-white overflow-hidden">
                <h4 className="px-4 py-3 text-sm font-semibold text-slate-700 border-b border-slate-200">
                    Dated Skill Events
                </h4>
                <div className="px-4 py-1">
                    {filteredDated.length === 0 ? (
                        <p className="py-4 text-sm text-slate-500">
                            {datedEvents.length === 0 ? "No dated skill events found" : "No matching dated events"}
                        </p>
                    ) : (
                        filteredDated.map((e, i) => (
                            <SkillsLogRow key={`${e.skill_name}-${e.project_name}-${i}`} {...e} date={e.date} />
                        ))
                    )}
                </div>
            </section>

            <section className="rounded-lg border border-slate-200 bg-white overflow-hidden">
                <h4 className="px-4 py-3 text-sm font-semibold text-slate-700 border-b border-slate-200">
                    Undated Skill Events
                </h4>
                <div className="px-4 py-1">
                    {filteredUndated.length === 0 ? (
                        <p className="py-4 text-sm text-slate-500">
                            {timeline.undated.length === 0 ? "No undated skill events found" : "No matching undated events"}
                        </p>
                    ) : (
                        filteredUndated.map((e, i) => (
                            <SkillsLogRow key={`${e.skill_name}-${e.project_name}-${i}`} {...e} />
                        ))
                    )}
                </div>
            </section>
        </div>
    );
}
