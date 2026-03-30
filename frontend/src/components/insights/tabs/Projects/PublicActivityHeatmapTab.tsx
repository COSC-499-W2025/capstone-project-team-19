import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { publicListProjects, publicGetActivityHeatmapData } from "../../../../api/public";
import type { PublicProject } from "../../../../api/public";
import type { ActivityHeatmapData } from "../../../../api/projects";
import { getColorForValue } from "./heatmapUtils";
import HeatmapLegend from "./HeatmapLegend";

export default function PublicActivityHeatmapTab({
    username,
    initialProjectId,
}: {
    username: string;
    /** From Insights URL (?project=) - selects this project when data loads */
    initialProjectId?: number;
}) {
    const [, setSearchParams] = useSearchParams();
    const [projects, setProjects] = useState<PublicProject[]>([]);
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [heatmap, setHeatmap] = useState<ActivityHeatmapData | null>(null);
    const [loading, setLoading] = useState(true);
    const [heatmapLoading, setHeatmapLoading] = useState(false);
    const [error, setError] = useState<string>("");

    useEffect(() => {
        let cancelled = false;
        publicListProjects(username)
            .then((list) => { if (!cancelled) setProjects(list); })
            .catch((e: Error) => { if (!cancelled) setError(e.message); })
            .finally(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, [username]);

    useEffect(() => {
        if (initialProjectId == null || projects.length === 0) return;
        const found = projects.some((p) => p.project_summary_id === initialProjectId);
        if (found) setSelectedId(initialProjectId);
    }, [projects, initialProjectId]);

    function syncProjectToUrl(projectId: number | null) {
        setSearchParams((prev) => {
            const next = new URLSearchParams(prev);
            next.set("view", "activity-heatmap");
            if (projectId != null) next.set("project", String(projectId));
            else next.delete("project");
            return next;
        });
    }

    function onSelectProject(projectId: number | null) {
        setSelectedId(projectId);
        syncProjectToUrl(projectId);
    }

    useEffect(() => {
        if (!selectedId) { setHeatmap(null); return; }
        let cancelled = false;
        setHeatmapLoading(true);
        publicGetActivityHeatmapData(username, selectedId)
            .then((data) => { if (!cancelled) setHeatmap(data); })
            .catch((e: Error) => { if (!cancelled) { setError(e.message); setHeatmap(null); } })
            .finally(() => { if (!cancelled) setHeatmapLoading(false); });
        return () => { cancelled = true; };
    }, [username, selectedId]);

    if (loading) return <div className="py-4 text-center text-slate-600">Loading projects...</div>;
    if (error && !heatmap) return <div className="py-4 text-center text-red-600">{error}</div>;
    if (projects.length === 0) return <div className="py-4 text-center text-slate-600">No projects available.</div>;

    const maxVal = heatmap ? Math.max(...heatmap.matrix.flat(), 1) : 1;

    return (
        <div className="flex flex-col gap-6 pt-4">
            <div className="flex flex-wrap items-center gap-4">
                <h3 className="text-lg font-semibold text-slate-800 m-0">Activity Heatmap</h3>
                <select
                    value={selectedId ?? ""}
                    onChange={(e) => {
                        const id = Number(e.target.value) || null;
                        onSelectProject(id);
                    }}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 min-w-[200px]"
                    aria-label="Select project"
                >
                    <option value="" disabled>Select a project</option>
                    {projects.map((p) => (
                        <option key={p.project_summary_id} value={p.project_summary_id}>
                            {p.project_name}
                        </option>
                    ))}
                </select>
            </div>

            {heatmapLoading && !heatmap ? (
                <div className="py-8 text-center text-slate-600">Loading heatmap...</div>
            ) : heatmap && heatmap.matrix.length > 0 ? (
                <section className="rounded-lg border border-slate-200 bg-white p-6 flex flex-col items-start w-fit self-start">
                    <h4 className="text-sm font-semibold text-slate-700 mb-4 m-0">{heatmap.project_name}</h4>
                    <div className="flex justify-center items-center">
                        <div
                            className="grid gap-0.5 text-sm"
                            style={{ gridTemplateColumns: `140px repeat(${heatmap.col_labels.length}, 3rem)` }}
                            role="grid"
                        >
                            <div className="pr-3" />
                            {heatmap.col_labels.map((l) => (
                                <div key={l} className="flex items-center justify-center py-1 text-slate-600 font-medium">
                                    {l}
                                </div>
                            ))}
                            {heatmap.matrix.map((row, i) => (
                                <div key={i} className="contents">
                                    <div className="pr-3 flex items-center justify-end text-slate-600 font-medium">
                                        {heatmap.row_labels[i]}
                                    </div>
                                    {row.map((v, j) => (
                                        <div
                                            key={`${i}-${j}`}
                                            className="w-12 h-12 rounded-sm flex items-center justify-center"
                                            style={{ backgroundColor: getColorForValue(v, maxVal) }}
                                            title={`${v.toFixed(1)}`}
                                            role="gridcell"
                                        />
                                    ))}
                                </div>
                            ))}
                        </div>
                    </div>
                    <HeatmapLegend />
                </section>
            ) : heatmap && heatmap.matrix.length === 0 ? (
                <div className="py-8 text-center text-slate-500">No heatmap data for this project.</div>
            ) : (
                <div className="py-8 text-center text-slate-500">Choose a project to view the activity heatmap!</div>
            )}
        </div>
    );
}
