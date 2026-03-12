import { useState, useMemo } from "react";
import type { SkillTimelineDTO, TimelineEventDTO } from "../../../../api/insights";
import { formatSkillName } from "./utils/formatHelpers";
import SkillBarsTable, { type SkillBarEntry, type SkillBarRowMeta } from "./SkillBarsTable";

type TotalsView = "all" | "code" | "text";

function aggregateUndatedBySkill(events: TimelineEventDTO[]): Map<string, SkillBarEntry & { skill_type?: "text" | "code" }> {
    const bySkill = new Map<string, SkillBarEntry & { skill_type?: "text" | "code" }>();
    for (const e of events) {
        const existing = bySkill.get(e.skill_name);
        if (existing) {
            existing.cumulative_score += e.score;
            existing.projects.push(e.project_name);
        } else {
            bySkill.set(e.skill_name, {
                cumulative_score: e.score,
                projects: [e.project_name],
                skill_type: e.skill_type,
            });
        }
    }
    return bySkill;
}

/** Earliest date string (from timeline.dated order) when skill first appears in a dated group */
function buildFirstDatedBySkill(timeline: SkillTimelineDTO): Map<string, string> {
    const map = new Map<string, string>();
    for (const group of timeline.dated) {
        const date = group.date;
        for (const ev of group.events) {
            if (!map.has(ev.skill_name)) map.set(ev.skill_name, date);
        }
        for (const skillName of Object.keys(group.cumulative_skills || {})) {
            if (!map.has(skillName)) map.set(skillName, date);
        }
    }
    return map;
}

export default function TotalsPanel({ timeline }: { timeline: SkillTimelineDTO }) {
    const [search, setSearch] = useState("");
    const [totalsView, setTotalsView] = useState<TotalsView>("all");

    const entries = Object.entries(timeline.current_totals);
    const undatedBySkill = useMemo(() => aggregateUndatedBySkill(timeline.undated), [timeline.undated]);
    const firstDatedBySkill = useMemo(() => buildFirstDatedBySkill(timeline), [timeline.dated]);

    const mergedEntries = useMemo(() => {
        const q = search.trim().toLowerCase();
        const result: [string, SkillBarEntry, SkillBarRowMeta][] = [];
        const currentKeys = new Set(entries.map(([k]) => k));

        for (const [skillName, data] of entries) {
            const matchesType = totalsView === "all" || data.skill_type === totalsView;
            const matchesSearch = q === "" || formatSkillName(skillName).toLowerCase().includes(q);
            if (!matchesType || !matchesSearch) continue;
            const firstAt = firstDatedBySkill.get(skillName);
            const meta: SkillBarRowMeta = firstAt
                ? { source: "dated", firstDatedAt: firstAt }
                : { source: "undated" };
            result.push([skillName, { cumulative_score: data.cumulative_score, projects: data.projects }, meta]);
        }

        for (const [skillName, data] of undatedBySkill) {
            if (currentKeys.has(skillName)) continue;
            const matchesType = totalsView === "all" || data.skill_type === totalsView;
            const matchesSearch = q === "" || formatSkillName(skillName).toLowerCase().includes(q);
            if (!matchesType || !matchesSearch) continue;
            result.push([skillName, { cumulative_score: data.cumulative_score, projects: data.projects }, { source: "undated" }]);
        }

        return result;
    }, [entries, undatedBySkill, firstDatedBySkill, totalsView, search]);

    const sorted = useMemo(() => [...mergedEntries].sort((a, b) => b[1].cumulative_score - a[1].cumulative_score), [mergedEntries]);
    const maxScore = Math.max(...mergedEntries.map(([, d]) => d.cumulative_score), 1);

    const totalsViewOptions: { value: TotalsView; label: string }[] = [
        { value: "all", label: "All" },
        { value: "code", label: "Code" },
        { value: "text", label: "Text" },
    ];
    const toggleBtn = (v: TotalsView) => totalsView === v ? "bg-slate-800 text-white" : "bg-white text-slate-800 hover:bg-slate-100";
    const hasAnyData = entries.length > 0 || timeline.undated.length > 0;

    if (!hasAnyData) {
        return (
            <div className="w-full py-3 bg-white px-4">
                <p>No totals.</p>
            </div>
        );
    }

    return (
        <div className="w-full py-3 px-4 bg-white">
            <div className="flex justify-between items-center gap-4 mt-2 mb-4 flex-wrap">
                <div className="flex-1 min-w-[200px] max-w-md">
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search skills..."
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
                    />
                </div>
                <div className="inline-flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white">
                    {totalsViewOptions.map(({ value, label }) => (
                        <button key={value} type="button" className={`border-none py-1.5 px-3 text-sm cursor-pointer ${toggleBtn(value)}`} onClick={() => setTotalsView(value)}>{label}</button>
                    ))}
                </div>
            </div>

            {mergedEntries.length === 0 ? (
                <p className="m-0">No matching skills found.</p>
            ) : (
                <SkillBarsTable entries={sorted} maxScore={maxScore} />
            )}
        </div>
    );
}
