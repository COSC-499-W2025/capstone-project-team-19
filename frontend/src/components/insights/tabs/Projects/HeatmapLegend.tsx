import { HEATMAP_COLORS } from "./heatmapUtils";

export default function HeatmapLegend() {
    return (
        <div className="flex items-center justify-center gap-2 mt-4 text-xs text-slate-500">
            <span>Less</span>
            {HEATMAP_COLORS.map((c, i) => (
                <span
                    key={i}
                    className="w-3 h-3 rounded-sm inline-block"
                    style={{ backgroundColor: c }}
                    aria-hidden
                />
            ))}
            <span>More</span>
        </div>
    );
}
