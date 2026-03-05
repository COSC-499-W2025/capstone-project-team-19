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
