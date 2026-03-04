import { useEffect, useState } from "react";
import { getProjectRanking } from "../../../api/insights";
import type { RankedProject } from "../../../api/insights";

export default function RankedProjectsTab() {
    const [rankings, setRankings] = useState<RankedProject[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>("");

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                setLoading(true);
                setError("");
                const data = await getProjectRanking();
                if (!cancelled) setRankings(data);
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

    if (loading) return <div className="ranked-state">Loading ranked projects...</div>;
    if (error) return <div className="ranked-state ranked-error">{error}</div>;
    if (rankings.length === 0) return <div className="ranked-state">No projects uploaded.</div>

    return (
        <section className="ranked-table">
            <div className="ranked-header">
                <div>PROJECT</div>
                <div>SCORE</div>
                <div>TYPE</div>
            </div>

            {rankings.map((p) => (
                <div key={p.project_summary_id} className="ranked-row">
                    <div>{p.project_name}</div>
                    <div>{p.score.toFixed(2)}</div>
                    <div>{p.manual_rank ? "MANUAL" : "AUTO"}</div>
                </div>
            ))}
        </section>
    )
}