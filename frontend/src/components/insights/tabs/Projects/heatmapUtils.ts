export const HEATMAP_COLORS = ["#ebedf0", "#93c5fd", "#60a5fa", "#3b82f6", "#2563eb"];

export function getColorForValue(value: number, maxVal: number): string {
    if (maxVal <= 0 || value <= 0) return HEATMAP_COLORS[0];
    const pct = value / maxVal;
    if (pct <= 0.25) return HEATMAP_COLORS[1];
    if (pct <= 0.5) return HEATMAP_COLORS[2];
    if (pct <= 0.75) return HEATMAP_COLORS[3];
    return HEATMAP_COLORS[4];
}
