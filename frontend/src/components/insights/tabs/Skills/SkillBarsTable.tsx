import { formatSkillName, toYMD } from "./utils/formatHelpers";

export type SkillProjectInfo = {
    name: string;
    date?: string | null;
};

export type SkillBarEntry = {
    cumulative_score: number;
    projects: SkillProjectInfo[];
};

type Props = {
    entries: [string, SkillBarEntry][];
    maxScore: number;
};

export default function SkillBarsTable({ entries, maxScore }: Props) {
    const sorted = [...entries].sort((a, b) => b[1].cumulative_score - a[1].cumulative_score);

    return (
        <>
            <div className="grid gap-x-2 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200 pb-2 mb-1" style={{ gridTemplateColumns: "minmax(0,1fr) 1fr 4rem" }}>
                <span>Skill</span>
                <span />
                <span className="text-right">Score</span>
            </div>
            <div className="flex flex-col">
                {sorted.map(([skillName, data], index) => {
                    const pct = (data.cumulative_score / maxScore) * 100;
                    const showTooltipAbove = index > 1;

                    return (
                        <div key={skillName} className="grid items-center gap-x-2 min-h-8 my-px" style={{ gridTemplateColumns: "minmax(0,1fr) 1fr 4rem" }}>
                            <div className="flex items-center gap-1.5 min-w-0 flex-wrap pr-0">
                                <span className="text-sm font-semibold opacity-90 truncate">{formatSkillName(skillName)}</span>                                
                            </div>

                            <div className="min-w-0 w-full">
                                <div className="group relative">
                                    <div className="w-full h-3.5 bg-slate-200 rounded overflow-hidden">
                                        <div className="h-full min-w-0 bg-slate-600 rounded transition-[width] duration-200" style={{ width: `${pct}%` }} />
                                    </div>

                                    {(data.projects?.length) ? (
                                        <div
                                            className={`hidden group-hover:block absolute left-0 w-50 bg-black text-white text-xs rounded-lg p-2 px-3 
                                                shadow-[0_14px_30px_rgba(0,0,0,0.3)] z-50 [&::after]:content-[''] 
                                                [&::after]:absolute [&::after]:left-[18px] [&::after]:w-0 [&::after]:h-0 [&::after]:border-l-[10px] 
                                                [&::after]:border-l-transparent [&::after]:border-r-[10px] [&::after]:border-r-transparent ${
                                                    showTooltipAbove
                                                        ? "bottom-full mb-2 [&::after]:border-t-[10px] [&::after]:border-t-black [&::after]:bottom-[-10px]"
                                                        : "top-full mt-2 [&::after]:border-b-[10px] [&::after]:border-b-black [&::after]:top-[-10px]"
                                                }`
                                            }
                                        >
                                            <div className="font-bold mb-2">{formatSkillName(skillName)}</div>
                                            
                                            <ul className="list-none p-0 m-0 grid gap-1.5">
                                                {data.projects.map((project, i) => (
                                                    <li key={`${project.name}-${i}`} className="flex justify-between gap-2.5 tabular-nums">
                                                        <span className="overflow-hidden text-ellipsis whitespace-nowrap max-w-[230px]">{project.name}</span>
                                                        <span className="shrink-0 text-xs text-white/80">{project.date ? toYMD(project.date) : "Undated"}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    ) : null}
                                </div>
                            </div>

                            <div className="tabular-nums text-right text-sm">
                                {typeof data.cumulative_score === "number"
                                    ? `${(data.cumulative_score * 100).toFixed(1)}%`
                                    : "—"}
                            </div>
                        </div>
                    );
                })}
            </div>
        </>
    );
}
