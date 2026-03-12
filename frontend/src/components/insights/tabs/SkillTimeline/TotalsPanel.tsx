import { useState, useMemo } from "react";
import type { SkillTimelineDTO } from "../../../../api/insights";
import { formatSkillName } from "./utils/formatHelpers";
import TimelineSortControls from "./TimelineSortControls";
import type { TimelineSortField, SortDirection } from "./utils/timelineSortTypes";

type TotalsView = "all" | "code" | "text";

export default function TotalsPanel({ timeline }: { timeline: SkillTimelineDTO }) {
    const [sortField, setSortField] = useState<TimelineSortField>("score");
    const [sortDir, setSortDir] = useState<SortDirection>("desc");
    const [totalsView, setTotalsView] = useState<TotalsView>("all");

    const entries = Object.entries(timeline.current_totals);

    //default toggle is all skill types (code/text)
    const filteredEntries = useMemo(() => {
        if (totalsView === "all") return entries;
        return entries.filter(([, data]) => data.skill_type === totalsView);
    }, [entries, totalsView]);

    if (entries.length === 0) return (
        <div className="w-full py-3 bg-white">
            <p>No totals.</p>
        </div>
    );

    const maxScore = Math.max(...filteredEntries.map(([, d]) => d.cumulative_score), 1);
    const sorted = [...filteredEntries].sort((a, b) => {
        if (sortField === "score") {
            const cmp = a[1].cumulative_score - b[1].cumulative_score;
            return sortDir === "asc" ? cmp : -cmp;
        }
        const cmp = a[0].toLowerCase().localeCompare(b[0].toLowerCase());
        return sortDir === "asc" ? cmp : -cmp;
    });

    const totalsViewOptions: { value: TotalsView; label: string }[] = [
        { value: "all", label: "All" },
        { value: "code", label: "Code" },
        { value: "text", label: "Text" },
    ];
    const toggleBtn = (v: TotalsView) => totalsView === v ? "bg-slate-800 text-white" : "bg-white text-slate-800 hover:bg-slate-100";

    return (
        <div className="w-full py-3 px-4">
            <div className="flex justify-between items-start gap-4 mb-4 flex-wrap">
                <TimelineSortControls sortField={sortField} setSortField={setSortField} sortDir={sortDir} setSortDir={setSortDir} fields={["skill_name", "score"]} />
                <div className="inline-flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white">
                    {totalsViewOptions.map(({ value, label }) => (
                        <button key={value} type="button" className={`border-none py-1.5 px-3 text-sm cursor-pointer ${toggleBtn(value)}`} onClick={() => setTotalsView(value)}>{label}</button>
                    ))}
                </div>
            </div>
            
            {filteredEntries.length === 0 ? (
                <p className="m-0">No {totalsView} skills available.</p>
            ) : sorted.map(([skillName, data]) => {
                const pct = (data.cumulative_score / maxScore) * 100;

                return (
                <div key={skillName} className="grid grid-cols-[220px_1fr_64px] items-center gap-px h-8 my-px">
                    <div className="text-sm font-semibold opacity-90">{formatSkillName(skillName)}</div>

                    <div className="min-w-0 w-full">
                        <div className="group relative">
                            <div className="w-full h-3.5 bg-slate-200 rounded overflow-hidden">
                                <div className="h-full min-w-0 bg-slate-600 rounded transition-[width] duration-200" style={{ width: `${pct}%` }} />
                            </div>

                            {data.projects?.length ? (
                            <div className="hidden group-hover:block absolute left-0 top-[-10px] -translate-y-full w-80 overflow-visible bg-black text-white rounded-lg p-2.5 px-3 shadow-[0_14px_30px_rgba(0,0,0,0.3)] z-50 [&::after]:content-[''] [&::after]:absolute [&::after]:left-[18px] [&::after]:bottom-[-10px] [&::after]:w-0 [&::after]:h-0 [&::after]:border-l-[10px] [&::after]:border-l-transparent [&::after]:border-r-[10px] [&::after]:border-r-transparent [&::after]:border-t-[10px] [&::after]:border-t-black">
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
    );
}