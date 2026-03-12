import { useEffect, useMemo, useState } from "react";
import { getRanking, replaceRankingOrder, resetRanking } from "../../../api/insights";
import type { RankedProject } from "../../../api/insights";

export default function RankedProjectsTab() {
    const [rankings, setRankings] = useState<RankedProject[]>([]);
    const [originalIds, setOriginalIds] = useState<number[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string>("");

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                setLoading(true);
                setError("");
                const res = await getRanking();
                const list = res.data.rankings;
                if (!cancelled) {
                    setRankings(list);
                    setOriginalIds(list.map((p) => p.project_summary_id));
                }
            }
            catch (e: any) {
                if (!cancelled) setError(e?.message ?? "Failed to load ranked projects");
            }
            finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, []);

    const currentIds = useMemo(
        () => rankings.map((p) => p.project_summary_id),
        [rankings]
    );

    const isDirty = useMemo(() => {
        if (originalIds.length !== currentIds.length) return true;

        for (let i = 0; i < originalIds.length; i++) {
            if (originalIds[i] !== currentIds[i]) return true;
        }
        return false;
    }, [originalIds, currentIds]);

    async function handleSaveOrder() {
        try {
            setSaving(true);
            setError("");

            const res = await replaceRankingOrder(currentIds);
            // backend returns fresh ranking order + manual ranks
            const list = res.data.rankings;
            setRankings(list);
            setOriginalIds(list.map((p) => p.project_summary_id));
        }
        catch (e: any) {
            setError(e?.message ?? "Failed to save ranking");
        }
        finally {
            setSaving(false);
        }
    }

    async function handleReset() {
        try {
            setSaving(true);
            setError("");

            const res = await resetRanking();
            const list = res.data.rankings;
            setRankings(list);
            setOriginalIds(list.map((p) => p.project_summary_id));
        }
        catch (e: any) {
            setError(e?.message ?? "Failed to reset ranking");
        }
        finally {
            setSaving(false);
        }
    }

    function move(index: number, dir: -1 | 1) {
        const newIndex = index + dir;
        if (newIndex < 0 || newIndex >= rankings.length) return;

        setRankings((prev) => {
            const copy = [...prev];
            const [item] = copy.splice(index, 1);
            copy.splice(newIndex, 0, item);
            return copy;
        });
    }

    if (loading) return <div className="py-4 text-center text-[#444]">Loading ranked projects...</div>;
    if (error) return <div className="py-4 text-center text-red-600">{error}</div>;
    if (rankings.length === 0) return <div className="py-4 text-center text-[#444]">No projects uploaded.</div>;

    const topThreeBar = (idx: number) => {
        if (idx === 0) return "bg-slate-700";
        if (idx === 1) return "bg-slate-600";
        if (idx === 2) return "bg-slate-500";
        return "bg-slate-400";
    };

    const TopBadge = ({ idx }: { idx: number }) => {
        if (idx > 2) return <span className="w-7 h-7 shrink-0" aria-hidden />;
        const styles = [
            "bg-slate-700 text-white font-black",
            "bg-slate-600 text-white font-black",
            "bg-slate-500 text-white font-black",
        ];
        return (
            <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm shrink-0 ${styles[idx]}`}>
                {idx + 1}
            </span>
        );
    };

    return (
        <section className="flex flex-col gap-4">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold">Ranked Projects</h3>
                <div className="flex gap-2">
                    <button
                        onClick={handleReset}
                        disabled={saving}
                        className="px-4 py-2 rounded-lg border-2 border-black bg-white font-medium cursor-pointer transition-all duration-150 hover:bg-black hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Reset to Auto
                    </button>
                    <button
                        onClick={handleSaveOrder}
                        disabled={!isDirty || saving}
                        className="px-4 py-2 rounded-lg border-2 border-black bg-white font-medium cursor-pointer transition-all duration-150 hover:bg-black hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {saving ? "Saving..." : "Save Order"}
                    </button>
                </div>
            </div>

            <div className="flex flex-col gap-3">
                {rankings.map((p, idx) => {
                    const pct = Math.min(p.score * 100, 100);
                    return (
                        <div
                            key={p.project_summary_id}
                            className={`grid grid-cols-[2rem_12rem_1fr_4rem_4.5rem] gap-x-4 items-center group rounded-lg px-2 py-1.5 -mx-2 transition-colors ${
                                idx < 3 ? "bg-blue-50/70" : "hover:bg-slate-50"
                            }`}
                        >
                            <div className="flex justify-center">
                                <TopBadge idx={idx} />
                            </div>
                            <span className="text-sm font-medium truncate">
                                {p.project_name}
                            </span>
                            <div className="min-w-0 h-8 rounded-full bg-slate-200 overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all duration-300 ${topThreeBar(idx)}`}
                                    style={{ width: `${Math.max(pct, 4)}%` }}
                                />
                            </div>
                            <span className="text-sm font-semibold tabular-nums text-right">
                                {p.score.toFixed(2)}
                            </span>
                            <div className="flex gap-0.5 opacity-60 group-hover:opacity-100 transition-opacity justify-end">
                                <button
                                    onClick={() => move(idx, -1)}
                                    disabled={idx === 0}
                                    className="w-8 h-8 flex items-center justify-center rounded border border-zinc-300 bg-white text-zinc-700 cursor-pointer transition-colors hover:bg-zinc-100 disabled:opacity-30 disabled:cursor-not-allowed"
                                    aria-label="Move up"
                                >
                                    ↑
                                </button>
                                <button
                                    onClick={() => move(idx, 1)}
                                    disabled={idx === rankings.length - 1}
                                    className="w-8 h-8 flex items-center justify-center rounded border border-zinc-300 bg-white text-zinc-700 cursor-pointer transition-colors hover:bg-zinc-100 disabled:opacity-30 disabled:cursor-not-allowed"
                                    aria-label="Move down"
                                >
                                    ↓
                                </button>
                            </div>
                        </div>
                    );
                })}
            </div>
        </section>
    );
}