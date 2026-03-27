import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { getActivityByDate } from "../../../../api/insights";
import { getColorForValue } from "./heatmapUtils";
import HeatmapLegend from "./HeatmapLegend";

function formatWeekLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

type TooltipState = {
  dateStr: string;
  dow: string;
  count: number;
  projects: string[];
  x: number;
  y: number;
} | null;

const LABEL_COL_PX = 20;
const GAP_PX = 2;
const MIN_CELL_PX = 8;
const MAX_CELL_PX = 14;

export default function ProjectSkillHeatmapTab() {
  const [data, setData] = useState<{
    title: string;
    row_labels: string[];
    col_labels: string[];
    matrix: number[][];
    available_years: number[];
    projects_by_date: Record<string, string[]>;
  } | null>(null);

  const [selectedYear, setSelectedYear] = useState<number | "all">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [tooltip, setTooltip] = useState<TooltipState>(null);
  const [cellPx, setCellPx] = useState(MAX_CELL_PX);

  const containerRef = useRef<HTMLDivElement>(null);

  // Recalculate cell size whenever container width or data changes
  useEffect(() => {
    if (!data) return;
    const cols = data.col_labels.length;
    if (cols === 0) return;

    function recalc() {
      if (!containerRef.current || !data) return;
      const available = containerRef.current.clientWidth - LABEL_COL_PX - GAP_PX * cols;
      const computed = Math.floor(available / cols);
      setCellPx(Math.min(MAX_CELL_PX, Math.max(MIN_CELL_PX, computed)));
    }

    recalc();

    const ro = new ResizeObserver(recalc);
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [data]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError("");
        const yearParam = selectedYear === "all" ? undefined : selectedYear;
        const result = await getActivityByDate(yearParam);
        if (!cancelled) setData(result);
      } catch (e: unknown) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load heatmap");
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [selectedYear]);

  if (loading) return <div className="py-4 text-center text-slate-600">Loading...</div>;
  if (error) return <div className="py-4 text-center text-red-600">{error}</div>;
  if (!data) return null;

  // Use min 4 so that 1 project = light shade, not dark (when max is 1, value/max would be 100%)
  const maxVal = data.matrix.length > 0 ? Math.max(...data.matrix.flat(), 4) : 4;
  const hasData = data.matrix.length > 0 && data.col_labels.length > 0;

  const cellSize = `${cellPx}px`;
  const gridTemplate = `${LABEL_COL_PX}px repeat(${data.col_labels.length}, ${cellSize})`;
  const gridGap = `${GAP_PX}px`;

  const tooltipEl =
    tooltip &&
    createPortal(
      <div
        className="pointer-events-none fixed z-[9999] whitespace-nowrap rounded-md bg-slate-800 px-3 py-2 text-sm text-white shadow-lg"
        style={{
          left: tooltip.x + 12,
          top: tooltip.y,
          transform: "translateY(-50%)",
        }}
      >
        <div className="font-medium">{tooltip.dateStr} ({tooltip.dow})</div>
        <div className="mt-0.5 text-slate-300">
          {tooltip.count > 0
            ? `${tooltip.count} project${tooltip.count !== 1 ? "s" : ""}`
            : "No contributions"}
        </div>
        {tooltip.projects.length > 0 && (
          <div className="mt-1.5 border-t border-slate-600 pt-1.5 text-xs text-slate-400">
            {tooltip.projects.join(", ")}
          </div>
        )}
      </div>,
      document.body
    );

  return (
    <div className="relative flex min-w-0 flex-col gap-6 pt-4">
      {tooltipEl}

      <div className="flex flex-wrap items-center gap-4">
        <div>
          <h3 className="m-0 text-lg font-semibold text-slate-800">Activity by Date</h3>
          <p className="m-0 mt-1 text-sm text-slate-500">
            See your activity over time. Select a year or view all data.
          </p>
        </div>

        {data.available_years.length > 0 && (
          <select
            value={selectedYear}
            onChange={(e) =>
              setSelectedYear(e.target.value === "all" ? "all" : Number(e.target.value))
            }
            className="min-w-[120px] rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
            aria-label="Select year"
          >
            <option value="all">All years</option>
            {data.available_years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        )}
      </div>

      {hasData ? (
        <section
          ref={containerRef}
          className="flex w-full flex-col rounded-lg border border-slate-200 bg-white p-5"
        >
          {/* week labels */}
          <div
            className="mb-3 grid text-[10px]"
            style={{ gridTemplateColumns: gridTemplate, gap: gridGap }}
          >
            <div aria-hidden />
            {data.col_labels.map((l, j) => (
              <div
                key={j}
                className="flex items-center justify-start overflow-hidden text-slate-400"
                title={l}
              >
                {j % 6 === 0 ? formatWeekLabel(l) : ""}
              </div>
            ))}
          </div>

          {/* heatmap grid */}
          <div
            className="grid text-xs"
            style={{ gridTemplateColumns: gridTemplate, gap: gridGap }}
            role="grid"
            aria-label="Activity heatmap by date"
          >
            {data.matrix.map((row, i) => (
              <div key={i} className="contents">
                <div
                  className="flex items-center justify-end pr-1 text-[10px] text-slate-500"
                  title={data.row_labels[i]}
                >
                  {data.row_labels[i][0]}
                </div>

                {row.map((v, j) => {
                  const weekStart = new Date(data.col_labels[j] + "T00:00:00");
                  const dayDate = new Date(weekStart);
                  dayDate.setDate(dayDate.getDate() + i);
                  const dateStr = dayDate.toISOString().slice(0, 10);
                  const dow = data.row_labels[i];
                  const projects = data.projects_by_date?.[dateStr] ?? [];

                  return (
                    <div
                      key={`${i}-${j}`}
                      className="cursor-pointer rounded-[2px]"
                      style={{
                        width: cellSize,
                        height: cellSize,
                        backgroundColor: getColorForValue(v, maxVal),
                      }}
                      onMouseEnter={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect();
                        setTooltip({
                          dateStr,
                          dow,
                          count: v,
                          projects,
                          x: rect.left + rect.width / 2,
                          y: rect.top,
                        });
                      }}
                      onMouseLeave={() => setTooltip(null)}
                      role="gridcell"
                      aria-label={
                        v > 0
                          ? `${dateStr} (${dow}): ${v} project${v !== 1 ? "s" : ""}`
                          : `${dateStr} (${dow}): No contributions`
                      }
                    />
                  );
                })}
              </div>
            ))}
          </div>

          <HeatmapLegend />
        </section>
      ) : (
        <div className="py-8 text-center text-slate-500">
          No activity data yet. Upload projects with dates set to see your activity heatmap.
        </div>
      )}
    </div>
  );
}