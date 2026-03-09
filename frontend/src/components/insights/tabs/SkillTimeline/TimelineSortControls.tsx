import type { TimelineSortField, SortDirection } from "./utils/timelineSortTypes";

const SORT_OPTIONS: { value: TimelineSortField; label: string }[] = [
    { value: "skill_name", label: "Skill name" },
    { value: "project_name", label: "Project" },
    { value: "level", label: "Level" },
    { value: "score", label: "Score" },
];

export default function TimelineSortControls({
    sortField,
    setSortField,
    sortDir,
    setSortDir,
    fields,
}: {
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

    return (
        <div className="skill-timeline-sort">
            <label>Sort by</label>
            <select value={sortField} onChange={(e) => setSortField(e.target.value as TimelineSortField)}>
                {options.map((o) => (
                    <option key={o.value} value={o.value}>
                        {o.label}
                    </option>
                ))}
            </select>

            <button
                type="button"
                className="skill-timeline-sort-dir"
                onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
                title={
                    sortField === "score"
                        ? sortDir === "asc"
                            ? "Low→High (click for High→Low)"
                            : "High→Low (click for Low→High)"
                        : sortDir === "asc"
                            ? "A→Z (click for Z→A)"
                            : "Z→A (click for A→Z)"
                }
            >
                {sortField === "score"
                    ? sortDir === "asc"
                        ? "Low→High"
                        : "High→Low"
                    : sortDir === "asc"
                        ? "A→Z"
                        : "Z→A"}
            </button>
        </div>
    );
}