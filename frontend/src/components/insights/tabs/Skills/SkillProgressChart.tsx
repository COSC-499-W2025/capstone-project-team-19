import { useState, useMemo } from "react";
import {LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer} from "recharts";    
import type { SkillTimelineDTO } from "../../../../api/insights";
import { formatSkillName, toShortDate } from "./utils/formatHelpers";

type DataPoint = { date: string; score: number; displayDate: string };

function buildChartData(timeline: SkillTimelineDTO, skillName: string): DataPoint[] {
    const points: DataPoint[] = [];
    for (const group of timeline.dated) {
        const cum = group.cumulative_skills[skillName];
        if (!cum) continue;
        points.push({
            date: group.date,
            score: cum.cumulative_score,
            displayDate: toShortDate(group.date),
        });
    }
    return points;
}

export default function SkillProgressChart({timeline,}: {timeline: SkillTimelineDTO;}) {
    const skillNames = timeline.summary.skill_names ?? [];
    const [selectedSkill, setSelectedSkill] = useState<string>(
        skillNames[0] ?? ""
    );

    const chartData = useMemo(
        () => (selectedSkill ? buildChartData(timeline, selectedSkill) : []),
        [timeline, selectedSkill]
    );

    if (skillNames.length === 0 || timeline.dated.length === 0) {
        return null;
    }

    return (
        <div className="w-full py-6 pb-4 bg-white border-b border-slate-200">
            <h3 className="text-base font-semibold text-slate-800 mb-3">
                Skill progress over time
            </h3>
            <p className="text-sm text-slate-600 mb-4">
                View how a skill&apos;s cumulative score has improved as you
                complete projects.
            </p>
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-4">
                <label
                    htmlFor="skill-select"
                    className="text-sm font-medium text-slate-700 shrink-0"
                >
                    Select skill:
                </label>
                <select
                    id="skill-select"
                    value={selectedSkill}
                    onChange={(e) => setSelectedSkill(e.target.value)}
                    className="block w-full sm:w-64 px-3 py-2 text-sm border border-slate-300 rounded-md bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                >
                    {skillNames.map((name) => (
                        <option key={name} value={name}>
                            {formatSkillName(name)}
                        </option>
                    ))}
                </select>
            </div>

            {chartData.length === 0 ? (
                <p className="text-sm text-slate-500 py-4">
                    No dated progress for this skill.
                </p>
            ) : (
                <div className="h-64 w-full min-w-0">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                            data={chartData}
                            margin={{
                                top: 5,
                                right: 10,
                                left: 0,
                                bottom: 5,
                            }}
                        >
                            <CartesianGrid
                                strokeDasharray="3 3"
                                stroke="rgb(226 232 240)"
                            />
                            <XAxis
                                dataKey="displayDate"
                                tick={{ fontSize: 11 }}
                                tickLine={false}
                                axisLine={{ stroke: "rgb(203 213 225)" }}
                                stroke="rgb(100 116 139)"
                            />
                            <YAxis
                                domain={[0, 1]}
                                tickFormatter={(v) => `${Math.round(v * 100)}%`}
                                tick={{ fontSize: 11 }}
                                tickLine={false}
                                axisLine={{ stroke: "rgb(203 213 225)" }}
                                stroke="rgb(100 116 139)"
                            />
                            <Tooltip
                                formatter={(value: number) => [
                                    `${Math.round((value as number) * 100)}%`,
                                    "Score",
                                ]}
                                labelFormatter={(label) => `Date: ${label}`}
                                contentStyle={{
                                    backgroundColor: "white",
                                    border: "1px solid rgb(226 232 240)",
                                    borderRadius: "6px",
                                    fontSize: "12px",
                                }}
                            />
                            <Line
                                type="monotone"
                                dataKey="score"
                                stroke="rgb(14 165 233)"
                                strokeWidth={2}
                                dot={{ fill: "rgb(14 165 233)", r: 4 }}
                                activeDot={{
                                    r: 6,
                                    fill: "rgb(14 165 233)",
                                    stroke: "white",
                                    strokeWidth: 2,
                                }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
}
