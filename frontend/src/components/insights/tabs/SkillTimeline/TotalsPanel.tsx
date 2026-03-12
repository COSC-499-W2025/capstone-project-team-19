import { useState, useMemo } from "react";
import type { SkillTimelineDTO } from "../../../../api/insights";
import { formatSkillName } from "./utils/formatHelpers";

type TotalsView = "all" | "code" | "text";

export default function TotalsPanel({ timeline }: { timeline: SkillTimelineDTO }) {
    const [search, setSearch] = useState("");
    const [totalsView, setTotalsView] = useState<TotalsView>("all");

    const entries = Object.entries(timeline.current_totals);

    const filteredEntries = useMemo(() => {
        const q = search.trim().toLowerCase();
        return entries.filter(([skillName, data]) => {
            const matchesType = totalsView === "all" || data.skill_type === totalsView;
            const matchesSearch = q === "" || formatSkillName(skillName).toLowerCase().includes(q);
            return matchesType && matchesSearch;
        });
    }, [entries, totalsView, search]);

    const sorted = useMemo(() => {
        return [...filteredEntries].sort((a, b) => b[1].cumulative_score - a[1].cumulative_score);
    }, [filteredEntries]);

    const maxScore = Math.max(...filteredEntries.map(([, d]) => d.cumulative_score), 1);

    const totalsViewOptions: { value: TotalsView; label: string }[] = [
        { value: "all", label: "All" },
        { value: "code", label: "Code" },
        { value: "text", label: "Text" },
    ];
    const toggleBtn = (v: TotalsView) => totalsView === v ? "bg-slate-800 text-white" : "bg-white text-slate-800 hover:bg-slate-100";

    if (entries.length === 0) {
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

            {filteredEntries.length === 0 ? (
                <p className="m-0">No matching skills found.</p>
            ) : (
                <>
                <div className="grid grid-cols-[220px_1fr_64px] gap-x-4 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200 pb-2 mb-1">
                    <span>Skill</span>
                    <span />
                    <span className="text-right">Score</span>
                </div>
                <div className="flex flex-col">
                    {sorted.map(([skillName, data], index) => {
                        const pct = (data.cumulative_score / maxScore) * 100;
                        const showTooltipAbove = index > 1;

                        return (
                            <div key={skillName} className="grid grid-cols-[220px_1fr_64px] items-center gap-x-4 h-8 my-px">
                                <div className="text-sm font-semibold opacity-90 truncate">{formatSkillName(skillName)}</div>

                                <div className="min-w-0 w-full">
                                    <div className="group relative">
                                        <div className="w-full h-3.5 bg-slate-200 rounded overflow-hidden">
                                            <div className="h-full min-w-0 bg-slate-600 rounded transition-[width] duration-200" style={{ width: `${pct}%` }} />
                                        </div>

                                        {data.projects?.length ? (
                                            <div
                                                className={`hidden group-hover:block absolute left-0 w-80 bg-black text-white rounded-lg p-2.5 px-3 shadow-[0_14px_30px_rgba(0,0,0,0.3)] z-50 [&::after]:content-[''] [&::after]:absolute [&::after]:left-[18px] [&::after]:w-0 [&::after]:h-0 [&::after]:border-l-[10px] [&::after]:border-l-transparent [&::after]:border-r-[10px] [&::after]:border-r-transparent ${
                                                    showTooltipAbove
                                                        ? "bottom-full mb-2 [&::after]:border-t-[10px] [&::after]:border-t-black [&::after]:bottom-[-10px]"
                                                        : "top-full mt-2 [&::after]:border-b-[10px] [&::after]:border-b-black [&::after]:top-[-10px]"
                                                }`}
                                            >
                                                <div className="font-bold mb-2">{formatSkillName(skillName)}</div>
                                                <ul className="list-none p-0 m-0 grid gap-1.5">
                                                    {data.projects.map((projectName, i) => (
                                                        <li key={`${projectName}-${i}`} className="flex justify-between gap-2.5 tabular-nums">
                                                            <span className="overflow-hidden text-ellipsis whitespace-nowrap max-w-[230px]">{projectName}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        ) : null}
                                    </div>
                                </div>

                                <div className="tabular-nums text-right text-sm">
                                    {typeof data.cumulative_score === "number"
                                        ? data.cumulative_score.toFixed(2)
                                        : "—"}
                                </div>
                            </div>
                        );
                    })}
                </div>
                </>
            )}
        </div>
    );
}
