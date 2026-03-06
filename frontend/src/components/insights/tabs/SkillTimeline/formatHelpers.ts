const MINOR_WORDS = new Set([
    "and", "or", "of", "the", "to", "in", "a", "an", "for", "with", "on", "at", "by",
]);

export function formatSkillName(name: string): string {
    return name
        .split(/\s+/)
        .map((word, i) => {
            const lower = word.toLowerCase();
            if (word.length > 1 && word === word.toUpperCase()) return word;
            if (MINOR_WORDS.has(lower) && i > 0) return lower;
            return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
        })
        .join(" ");
}

export function toYMD(iso?: string | null) {
    if (!iso) return "";

    const d = new Date(iso);

    const formatted = d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });

    // add the period after the month abbreviation
    return formatted.replace(/^(\w{3})/, "$1.");
}