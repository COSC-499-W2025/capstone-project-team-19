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

    if (loading) return <div className="ranked-state">Loading ranked projects...</div>;
    if (error) return <div className="ranked-state ranked-error">{error}</div>;
    if (rankings.length === 0) return <div className="ranked-state">No projects uploaded.</div>

    return (
        <section className="ranked-table">
            <div className="ranked-toolbar">
                <div className="ranked-title">Ranked Projects</div>

                <div className="ranked-toolbar-actions">
                    <button onClick={handleReset} disabled={saving}>Reset to Auto</button>
                    <button onClick={handleSaveOrder} disabled={!isDirty || saving}>{saving ? "Saving..." : "Save Order"}</button>
                </div>
            </div>

            <div className="ranked-header">
                <div>PROJECT</div>
                <div>SCORE</div>
                <div>RANK</div>
                <div>ORDER</div>
            </div>

            {rankings.map((p, idx) => (
                <div key={p.project_summary_id} className="ranked-row">
                    <div>{p.project_name}</div>
                    <div>{p.score.toFixed(2)}</div>
                    <div>{p.manual_rank != null ? "MANUAL" : "AUTO"}</div>

                    <div className="ranked-row-actions">
                        <button onClick={() => move(idx, -1)} disabled={idx === 0}>↑</button>
                        <button onClick={() => move(idx, 1)} disabled={idx === rankings.length - 1}>↓</button>
                    </div>
                </div>
            ))}
            </section>
    )
}