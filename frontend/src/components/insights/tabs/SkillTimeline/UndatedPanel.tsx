import { useState, useMemo } from "react";
import type { TimelineEventDTO } from "../../../../api/insights";
import { formatSkillName } from "./utils/formatHelpers";
import SkillBarsTable from "./SkillBarsTable";

export default function UndatedPanel({ events, embedded }: { events: TimelineEventDTO[]; embedded?: boolean }) {
    const [search, setSearch] = useState("");

    const aggregated = useMemo(() => {
        const bySkill = new Map<string, { cumulative_score: number; projects: string[] }>();
        for (const e of events) {
            const existing = bySkill.get(e.skill_name);
            if (existing) {
                existing.cumulative_score += e.score;
                existing.projects.push(e.project_name);
            } else {
                bySkill.set(e.skill_name, { cumulative_score: e.score, projects: [e.project_name] });
            }
        }
        return Object.entries(Object.fromEntries(bySkill));
    }, [events]);

    const filteredEntries = useMemo(() => {
        const q = search.trim().toLowerCase();
        if (q === "") return aggregated;
        return aggregated.filter(([skillName]) =>
            formatSkillName(skillName).toLowerCase().includes(q)
        );
    }, [aggregated, search]);

    const maxScore = Math.max(...filteredEntries.map(([, d]) => d.cumulative_score), 1);

    if (events.length === 0) {
        return (
            <div className="w-full py-3 bg-white px-4">
                <p>No undated events.</p>
            </div>
        );
    }

    return (
        <div className={embedded ? "w-full bg-white" : "w-full py-3 px-4 bg-white"}>
            <div className={`flex justify-between items-center gap-4 flex-wrap ${embedded ? "mb-4" : "mt-2 mb-4"}`}>
                <div className="flex-1 min-w-[200px] max-w-md">
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search skills..."
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
                    />
                </div>
            </div>

            {filteredEntries.length === 0 ? (
                <p className="m-0">No matching skills found.</p>
            ) : (
                <SkillBarsTable
                    entries={filteredEntries.map(([name, data]) => [name, data, { source: "undated" as const }])}
                    maxScore={maxScore}
                />
            )}
        </div>
    );
}
