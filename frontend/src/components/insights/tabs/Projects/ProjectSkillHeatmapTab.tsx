import { useEffect, useState } from "react";
import { getProjectSkillMatrix } from "../../../../api/insights";

const HEATMAP_COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"];

function getColorForValue(value: number, maxVal: number): string {
    if (maxVal <= 0 || value <= 0) return HEATMAP_COLORS[0];
    const pct = value / maxVal;
    if (pct <= 0.25) return HEATMAP_COLORS[1];
    if (pct <= 0.5) return HEATMAP_COLORS[2];
    if (pct <= 0.75) return HEATMAP_COLORS[3];
    return HEATMAP_COLORS[4];
}

export default function ProjectSkillHeatmapTab() {
    const [data, setData] = useState<{ title: string; row_labels: string[]; col_labels: string[]; matrix: number[][] } | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>("");

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                setLoading(true);
                setError("");
                const result = await getProjectSkillMatrix();
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
    }, []);

    if (loading) return <div className="py-4 text-center text-slate-600">Loading...</div>;
    if (error) return <div className="py-4 text-center text-red-600">{error}</div>;
    if (!data) return null;

    const maxVal = data.matrix.length > 0 ? Math.max(...data.matrix.flat(), 1) : 1;

    return (
        <div className="flex flex-col gap-6 pt-4">
            <div>
                <h3 className="text-lg font-semibold text-slate-800 m-0">Skills Across Projects</h3>
                <p className="text-sm text-slate-500 mt-1 m-0">
                    See how skills are distributed across your projects.
                </p>
            </div>

            {data.matrix.length > 0 && data.col_labels.length > 0 ? (
                <section className="rounded-lg border border-slate-200 bg-white p-6 flex flex-col items-start w-fit self-start overflow-x-auto max-w-full">
                    <div
                        className="grid gap-0.5 text-sm"
                        style={{ gridTemplateColumns: `minmax(220px, max-content) repeat(${data.col_labels.length}, minmax(7rem, 9rem))` }}
                        role="grid"
                    >
                        <div className="pr-3" />
                        {data.col_labels.map((l) => (
                            <div
                                key={l}
                                className="flex items-center justify-center py-1 px-1 text-slate-600 font-medium text-center break-words min-h-[2.5rem]"
                                title={l}
                            >
                                {l}
                            </div>
                        ))}
                        {data.matrix.map((row, i) => (
                            <div key={i} className="contents">
                                <div className="pr-3 flex items-center justify-end text-slate-600 font-medium whitespace-nowrap" title={data.row_labels[i]}>
                                    {data.row_labels[i]}
                                </div>
                                {row.map((v, j) => (
                                    <div
                                        key={`${i}-${j}`}
                                        className="w-12 h-12 rounded-sm flex items-center justify-center"
                                        style={{ backgroundColor: getColorForValue(v, maxVal) }}
                                        title={`${data.row_labels[i]} / ${data.col_labels[j]}: ${v.toFixed(2)}`}
                                        role="gridcell"
                                    />
                                ))}
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
                    No data yet. Upload projects with skills to see the heatmap.
                </div>
            )}
        </div>
    );
}
