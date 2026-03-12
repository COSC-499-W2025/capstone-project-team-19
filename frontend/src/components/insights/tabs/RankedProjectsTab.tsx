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
            catch (e: unknown) {
                if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load ranked projects");
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

    const currentIds = useMemo(() => rankings.map((p) => p.project_summary_id), [rankings]);

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
        catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to save ranking");
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
        catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to reset ranking");
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

    if (loading) return <div className="py-4 text-center text-slate-600">Loading ranked projects...</div>;
    if (error) return <div className="py-4 text-center text-red-600">{error}</div>;
    if (rankings.length === 0) return <div className="py-4 text-center text-slate-600">No projects uploaded.</div>;

    const topThreeBar = (idx: number) => {
        if (idx === 0) return "bg-slate-700";
        if (idx === 1) return "bg-slate-600";
        if (idx === 2) return "bg-slate-500";
        return "bg-slate-300";
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

    const actionBtn = "px-4 py-2 rounded-lg border-2 border-slate-600 bg-white font-medium cursor-pointer transition-all duration-150 hover:bg-slate-600 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed";
    const moveBtn = "w-9 h-9 flex items-center justify-center rounded-lg border-2 border-slate-300 bg-white text-slate-600 font-bold text-sm cursor-pointer transition-all hover:bg-slate-100 hover:border-slate-400 hover:text-slate-800 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-slate-300";

    return (
        <section className="flex flex-col gap-5">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Ranked Projects</h3>
                <div className="flex gap-2">
                    <button onClick={handleReset} disabled={saving} className={actionBtn}>Reset to Auto</button>
                    <button onClick={handleSaveOrder} disabled={!isDirty || saving} className={actionBtn}>{saving ? "Saving..." : "Save Order"}</button>
                </div>
            </div>

            <div className="flex flex-col gap-3">
                {rankings.map((p, idx) => {
                    const pct = Math.min(p.score * 100, 100);
                    const rowClass = `grid grid-cols-[2rem_12rem_1fr_4rem_5rem] gap-x-4 items-center group rounded-lg px-2 py-1.5 -mx-2 transition-colors ${idx < 3 ? "bg-sky-50" : "hover:bg-slate-50"}`;
                    return (
                        <div key={p.project_summary_id} className={rowClass}>
                            <div className="flex justify-center"><TopBadge idx={idx} /></div>
                            <span className="text-sm font-medium truncate">{p.project_name}</span>
                            <div className="min-w-0 h-8 rounded-full bg-slate-100 overflow-hidden">
                                <div className={`h-full rounded-full transition-all duration-300 ${topThreeBar(idx)}`} style={{ width: `${Math.max(pct, 4)}%` }} />
                            </div>
                            <span className="text-sm font-semibold tabular-nums text-right">{p.score.toFixed(2)}</span>
                            <div className="flex gap-1 justify-end">
                                <button onClick={() => move(idx, -1)} disabled={idx === 0} className={moveBtn} aria-label="Move up">↑</button>
                                <button onClick={() => move(idx, 1)} disabled={idx === rankings.length - 1} className={moveBtn} aria-label="Move down">↓</button>
                            </div>
                        </div>
                    );
                })}
            </div>
        </section>
    );
}