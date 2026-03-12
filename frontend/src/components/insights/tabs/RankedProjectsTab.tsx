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
    if (rankings.length === 0) return <div className="py-4 text-center text-[#444]">No projects uploaded.</div>

    return (
        <section className="flex flex-col gap-2.5">
            <div className="flex justify-between items-center mb-4">
                <div className="text-lg font-bold">Ranked Projects</div>

                <div className="flex gap-2.5">
                    <button
                        onClick={handleReset}
                        disabled={saving}
                        className="px-3.5 py-2 rounded-md border-2 border-black bg-white font-medium cursor-pointer transition-all duration-150 hover:bg-black hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Reset to Auto
                    </button>
                    <button
                        onClick={handleSaveOrder}
                        disabled={!isDirty || saving}
                        className="px-3.5 py-2 rounded-md border-2 border-black bg-white font-medium cursor-pointer transition-all duration-150 hover:bg-black hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {saving ? "Saving..." : "Save Order"}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-[2fr_1fr_1fr_auto] font-semibold text-[15px] tracking-wide text-[#444] mx-1.5">
                <div>PROJECT</div>
                <div>SCORE</div>
                <div>RANK</div>
                <div>ORDER</div>
            </div>

            {rankings.map((p, idx) => (
                <div
                    key={p.project_summary_id}
                    className="grid grid-cols-[2fr_1fr_1fr_auto] bg-[#d4caca] rounded-md p-3 items-center border border-[#9f9494]"
                >
                    <div>{p.project_name}</div>
                    <div>{p.score.toFixed(2)}</div>
                    <div>{p.manual_rank != null ? "MANUAL" : "AUTO"}</div>

                    <div className="flex gap-1.5">
                        <button
                            onClick={() => move(idx, -1)}
                            disabled={idx === 0}
                            className="border-none bg-white text-base cursor-pointer p-1.5 rounded transition-colors duration-150 hover:bg-[#e6e6e6] disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            ↑
                        </button>
                        <button
                            onClick={() => move(idx, 1)}
                            disabled={idx === rankings.length - 1}
                            className="border-none bg-white text-base cursor-pointer p-1.5 rounded transition-colors duration-150 hover:bg-[#e6e6e6] disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            ↓
                        </button>
                    </div>
                </div>
            ))}
        </section>
    )
}