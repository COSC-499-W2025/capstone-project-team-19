import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { getActivityByDate } from "../../../../api/insights";

const HEATMAP_COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"];

function getColorForValue(value: number, maxVal: number): string {
    if (maxVal <= 0 || value <= 0) return HEATMAP_COLORS[0];
    const pct = value / maxVal;
    if (pct <= 0.25) return HEATMAP_COLORS[1];
    if (pct <= 0.5) return HEATMAP_COLORS[2];
    if (pct <= 0.75) return HEATMAP_COLORS[3];
    return HEATMAP_COLORS[4];
}

function formatWeekLabel(dateStr: string): string {
    const d = new Date(dateStr + "T00:00:00");
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

type TooltipState = {
    dateStr: string;
    dow: string;
    count: number;
    projects: string[];
    x: number;
    y: number;
} | null;

export default function ProjectSkillHeatmapTab() {
    const [data, setData] = useState<{ title: string; row_labels: string[]; col_labels: string[]; matrix: number[][]; available_years: number[]; projects_by_date: Record<string, string[]> } | null>(null);
    const [selectedYear, setSelectedYear] = useState<number | "all">("all");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>("");
    const [tooltip, setTooltip] = useState<TooltipState>(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                setLoading(true);
                setError("");
                const yearParam = selectedYear === "all" ? undefined : selectedYear;
                const result = await getActivityByDate(yearParam);
                if (!cancelled) setData(result);
            } catch (e: unknown) {
                if (!cancelled) {
                    setError(e instanceof Error ? e.message : "Failed to load heatmap");
                    setData(null);
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => { cancelled = true; };
    }, [selectedYear]);

    if (loading) return <div className="py-4 text-center text-slate-600">Loading...</div>;
    if (error) return <div className="py-4 text-center text-red-600">{error}</div>;
    if (!data) return null;

    const maxVal = data.matrix.length > 0 ? Math.max(...data.matrix.flat(), 1) : 1;
    const hasData = data.matrix.length > 0 && data.col_labels.length > 0;

    const tooltipEl = tooltip && createPortal(
        <div
            className="fixed z-[9999] pointer-events-none py-2 px-3 rounded-md bg-slate-800 text-white text-sm shadow-lg whitespace-nowrap"
            style={{
                left: tooltip.x + 12,
                top: tooltip.y,
                transform: "translateY(-50%)",
            }}
        >
            <div className="font-medium">{tooltip.dateStr} ({tooltip.dow})</div>
            <div className="text-slate-300 mt-0.5">
                {tooltip.count > 0 ? `${tooltip.count} project${tooltip.count !== 1 ? "s" : ""}` : "No contributions"}
            </div>
            {tooltip.projects.length > 0 && (
                <div className="mt-1.5 text-xs text-slate-400 border-t border-slate-600 pt-1.5">
                    {tooltip.projects.join(", ")}
                </div>
            )}
        </div>,
        document.body
    );

    return (
        <div className="flex flex-col gap-6 pt-4 relative">
            {tooltipEl}
            <div className="flex flex-wrap items-center gap-4">
                <div>
                    <h3 className="text-lg font-semibold text-slate-800 m-0">Activity by Date</h3>
                    <p className="text-sm text-slate-500 mt-1 m-0">
                        See your activity over time. Select a year or view all data.
                    </p>
                </div>
                {data.available_years.length > 0 && (
                    <select
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(e.target.value === "all" ? "all" : Number(e.target.value))}
                        className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 min-w-[120px]"
                        aria-label="Select year"
                    >
                        <option value="all">All years</option>
                        {data.available_years.map((y) => (
                            <option key={y} value={y}>{y}</option>
                        ))}
                    </select>
                )}
            </div>

            {hasData ? (
                <section className="rounded-lg border border-slate-200 bg-white p-6 flex flex-col items-start w-fit self-start overflow-x-auto max-w-full">
                    {/* Week labels in separate row above the grid to avoid overlap */}
                    <div
                        className="grid gap-[3px] text-xs mb-4"
                        style={{ gridTemplateColumns: `1.5rem repeat(${data.col_labels.length}, 1rem)` }}
                    >
                        <div aria-hidden />
                        {data.col_labels.map((l, j) => (
                            <div
                                key={j}
                                className="flex items-center justify-center text-slate-400 font-medium h-4"
                                title={l}
                            >
                                {j % 4 === 0 ? formatWeekLabel(l) : ""}
                            </div>
                        ))}
                    </div>
                    <div
                        className="grid gap-[3px] text-xs"
                        style={{ gridTemplateColumns: `1.5rem repeat(${data.col_labels.length}, 1rem)` }}
                        role="grid"
                        aria-label="Activity heatmap by date"
                    >
                        {data.matrix.map((row, i) => (
                            <div key={i} className="contents">
                                <div
                                    className="pr-1 flex items-center justify-end text-slate-500 text-[10px]"
                                    title={data.row_labels[i]}
                                >
                                    {data.row_labels[i][0]}
                                </div>
                                {row.map((v, j) => {
                                    const weekStart = new Date(data.col_labels[j] + "T00:00:00");
                                    const dayDate = new Date(weekStart);
                                    dayDate.setDate(dayDate.getDate() + i);
                                    const dateStr = dayDate.toISOString().slice(0, 10);
                                    const dow = data.row_labels[i];
                                    const projects = data.projects_by_date?.[dateStr] ?? [];
                                    return (
                                        <div
                                            key={`${i}-${j}`}
                                            className="w-4 h-4 rounded-[2px] min-w-[1rem] min-h-[1rem] cursor-pointer"
                                            style={{ backgroundColor: getColorForValue(v, maxVal) }}
                                            onMouseEnter={(e) => {
                                                const rect = e.currentTarget.getBoundingClientRect();
                                                setTooltip({
                                                    dateStr,
                                                    dow,
                                                    count: v,
                                                    projects,
                                                    x: rect.left + rect.width / 2,
                                                    y: rect.top,
                                                });
                                            }}
                                            onMouseLeave={() => setTooltip(null)}
                                            role="gridcell"
                                            aria-label={v > 0 ? `${dateStr} (${dow}): ${v} project${v !== 1 ? "s" : ""}` : `${dateStr} (${dow}): No contributions`}
                                        />
                                    );
                                })}
                            </div>
                        ))}
                    </div>
                    <div className="flex items-center justify-center gap-2 mt-4 text-xs text-slate-500">
                        <span>Less</span>
                        {HEATMAP_COLORS.map((c, i) => (
                            <span
                                key={i}
                                className="w-3 h-3 rounded-sm inline-block"
                                style={{ backgroundColor: c }}
                                aria-hidden
                            />
                        ))}
                        <span>More</span>
                    </div>
                </section>
            ) : (
                <div className="py-8 text-center text-slate-500">
                    No activity data yet. Upload projects with dates set to see your activity heatmap.
                </div>
            )}
        </div>
    );
}
