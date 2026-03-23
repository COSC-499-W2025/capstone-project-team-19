import { Star } from "lucide-react";

/** Maps level string to number of stars: Beginner=1, Intermediate=2, Advanced=3, Expert=3 */
function levelToStarCount(level: string): number {
    const normalized = level.trim().toLowerCase();
    if (normalized === "beginner") return 1;
    if (normalized === "intermediate") return 2;
    if (normalized === "advanced" || normalized === "expert") return 3;
    return 2; // default to intermediate for unknown
}

/** Returns the display label for a level (for tooltips/accessibility) */
export function levelToLabel(level: string): string {
    const normalized = level.trim();
    if (normalized.length === 0) return "";
    return normalized.charAt(0).toUpperCase() + normalized.slice(1).toLowerCase();
}

type LevelStarsProps = {
    level: string;
    className?: string;
    size?: "sm" | "md";
};

const MAX_STARS = 3;

export default function LevelStars({ level, className = "", size = "md" }: LevelStarsProps) {
    const count = levelToStarCount(level);
    const label = levelToLabel(level);
    const iconSize = size === "sm" ? 12 : 14;

    return (
        <span
            className={`inline-flex items-center gap-0.5 ${className}`}
            title={label}
            role="img"
            aria-label={`${label} (${count} of ${MAX_STARS} stars)`}
        >
            {Array.from({ length: MAX_STARS }).map((_, i) => {
                const filled = i < count;
                return (
                    <Star
                        key={i}
                        size={iconSize}
                        className={filled
                            ? "fill-sky-500 text-sky-500"
                            : "fill-slate-300 text-slate-300"
                        }
                        strokeWidth={2}
                        aria-hidden
                    />
                );
            })}
        </span>
    );
}
