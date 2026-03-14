import { useEffect, useMemo, useRef, useState } from "react";
import { getRanking, replaceRankingOrder, resetRanking } from "../../../../api/insights";
import type { RankedProject } from "../../../../api/insights";
import { useInsightsHeaderActions } from "../../InsightsHeaderActionsContext";

const actionBtn =
	"px-4 py-0 rounded-lg border-2 border-slate-600 bg-white font-medium cursor-pointer transition-all duration-150 hover:bg-slate-600 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed";
const moveBtn =
	"w-6 h-6 flex items-center justify-center rounded border border-slate-300 bg-white text-slate-600 font-bold text-xs cursor-pointer transition-all hover:bg-slate-100 hover:border-slate-400 hover:text-slate-800 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-slate-300 shrink-0";

const BAR_COLORS = ["bg-slate-700", "bg-slate-600", "bg-slate-500", "bg-slate-300"];
const BADGE_STYLES = ["bg-slate-700 text-white font-black", "bg-slate-600 text-white font-black", "bg-slate-500 text-white font-black"];

function TopBadge({ idx }: { idx: number }) {
	if (idx > 2) return <span className="w-7 h-7 shrink-0" aria-hidden />;
	return (
		<span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm shrink-0 ${BADGE_STYLES[idx]}`}>
			{idx + 1}
		</span>
	);
}

export default function RankedProjectsTab() {
	const [rankings, setRankings] = useState<RankedProject[]>([]);
	const [originalIds, setOriginalIds] = useState<number[]>([]);
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);
	const [error, setError] = useState<string>("");

	const setHeaderActions = useInsightsHeaderActions()?.setActions;

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
			} catch (e: unknown) {
				if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load ranked projects");
			} finally {
				if (!cancelled) setLoading(false);
			}
		}

		load();
		return () => {
			cancelled = true;
		};
	}, []);

	const currentIds = useMemo(() => rankings.map((p) => p.project_summary_id), [rankings]);
	const currentIdsRef = useRef(currentIds);
	currentIdsRef.current = currentIds;

	const isDirty = useMemo(
		() => originalIds.length !== currentIds.length || originalIds.some((id, i) => id !== currentIds[i]),
		[originalIds, currentIds]
	);

	function applyRankingResult(list: RankedProject[]) {
		setRankings(list);
		setOriginalIds(list.map((p) => p.project_summary_id));
	}

	async function handleSaveOrder() {
		try {
			setSaving(true);
			setError("");
			const idsToSave = currentIdsRef.current;
			const res = await replaceRankingOrder(idsToSave);
			applyRankingResult(res.data.rankings);
		} catch (e: unknown) {
			setError(e instanceof Error ? e.message : "Failed to save ranking");
		} finally {
			setSaving(false);
		}
	}

	async function handleReset() {
		try {
			setSaving(true);
			setError("");
			const res = await resetRanking();
			applyRankingResult(res.data.rankings);
		} catch (e: unknown) {
			setError(e instanceof Error ? e.message : "Failed to reset ranking");
		} finally {
			setSaving(false);
		}
	}

	useEffect(() => {
		if (loading || error || rankings.length === 0) {
			setHeaderActions?.(null);
			return () => setHeaderActions?.(null);
		}
		setHeaderActions?.(
			<div className="flex flex-1 justify-end gap-2">
				<button onClick={handleReset} disabled={saving} className={actionBtn}>Reset Ranking</button>
				<button onClick={handleSaveOrder} disabled={!isDirty || saving} className={actionBtn}>{saving ? "Saving..." : "Save Ranking"}</button>
			</div>
		);
		return () => setHeaderActions?.(null);
	}, [setHeaderActions, loading, error, rankings.length, isDirty, saving]);

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

	return (
		<section className="flex flex-col gap-3 pt-4">
			<div className="flex flex-col gap-3 w-fit">
				{rankings.map((p, idx) => {
					const pct = Math.min(p.score * 100, 100);
					const rowClass = `ranked-row grid grid-cols-[2.5rem_14rem_minmax(15rem,42rem)_5rem] gap-x-4 items-center group rounded px-3 py-2 -mx-3 transition-colors ${idx < 3 ? "bg-sky-50" : "hover:bg-slate-50"}`;
					return (
						<div key={p.project_summary_id} className={rowClass}>
							<div className="flex justify-center"><TopBadge idx={idx} /></div>
							<span className="text-sm font-medium truncate">{p.project_name}</span>
							<div className="min-w-0 flex items-center gap-2">
								<div className="flex gap-0.5 shrink-0">
									<button onClick={() => move(idx, -1)} disabled={idx === 0} className={moveBtn} aria-label="Move up">↑</button>
									<button onClick={() => move(idx, 1)} disabled={idx === rankings.length - 1} className={moveBtn} aria-label="Move down">↓</button>
								</div>
								<div className="flex-1 h-4 rounded-full bg-stone-200 overflow-hidden min-w-0">
									<div className={`h-full rounded-full transition-all duration-300 ${BAR_COLORS[Math.min(idx, 3)]}`} style={{ width: `${Math.max(pct, 4)}%` }} />
								</div>
							</div>
							<span className="text-sm font-semibold tabular-nums text-right">{p.score.toFixed(2)}</span>
						</div>
					);
				})}
			</div>
		</section>
	);
}
