import type { TimelineEventDTO } from "../../../../api/insights";
import { formatSkillName, toShortDate } from "./utils/formatHelpers";
import LevelStars from "./LevelStars";

export type EventWithDate = TimelineEventDTO & { date?: string };

export default function SkillsLogRow({ skill_name, project_name, level, score, date }: EventWithDate) {
    return (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-0.5 py-2.5 border-b border-slate-100 last:border-b-0">
            <div>
                <div className="font-semibold text-slate-900">{formatSkillName(skill_name)}</div>
                <div className="text-sm text-slate-500">
                    {project_name} · <LevelStars level={level} size="sm" /> · {score.toFixed(2)}
                </div>
            </div>
            {date && (
                <span className="text-xs text-slate-400 sm:text-slate-500 sm:shrink-0">
                    {toShortDate(date)}
                </span>
            )}
        </div>
    );
}
