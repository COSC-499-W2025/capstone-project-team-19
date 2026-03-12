import type { TimelineSortField, SortDirection } from "./utils/timelineSortTypes";

const SORT_OPTIONS: { value: TimelineSortField; label: string }[] = [
    { value: "skill_name", label: "Skill name" },
    { value: "project_name", label: "Project" },
    { value: "level", label: "Level" },
    { value: "score", label: "Score" },
];

export default function TimelineSortControls({ sortField, setSortField, sortDir, setSortDir, fields, }: {
    sortField: TimelineSortField;
    setSortField: (f: TimelineSortField) => void;
    sortDir: SortDirection;
    setSortDir: React.Dispatch<React.SetStateAction<SortDirection>>;
    /** If set, only show these options (e.g. Totals panel uses ["skill_name", "score"]). */
    fields?: readonly TimelineSortField[];
}) {
    const options = fields
        ? SORT_OPTIONS.filter((o) => (fields as readonly string[]).includes(o.value))
        : SORT_OPTIONS;

    const isScore = sortField === "score";
    const dirLabel = isScore ? (sortDir === "asc" ? "Low→High" : "High→Low") : (sortDir === "asc" ? "A→Z" : "Z→A");
    const title = `${dirLabel} (click for ${sortDir === "asc" ? (isScore ? "High→Low" : "Z→A") : isScore ? "Low→High" : "A→Z"})`;

    return (
        <div className="flex items-center gap-2.5 mb-4">
            <label className="text-sm text-slate-600">Sort by</label>
            <select value={sortField} onChange={(e) => setSortField(e.target.value as TimelineSortField)} className="py-1.5 px-2.5 text-sm border border-slate-300 rounded-md bg-white">
                {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <button type="button" className="py-1.5 px-3 text-sm border border-slate-300 rounded-md bg-white cursor-pointer hover:bg-slate-100" onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))} title={title}>
                {dirLabel}
            </button>
        </div>
    );
}