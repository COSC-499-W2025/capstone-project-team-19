import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { GitHubRepo } from "../../../../api/uploads";

type Props = {
  repos: GitHubRepo[];
  selectedRepo: string;
  onSelect: (fullName: string) => void;
  disabled?: boolean;
};

function ChevronIcon({ direction }: { direction: "up" | "down" }) {
  const d = direction === "up" ? "M3 10 L8 5 L13 10 Z" : "M3 6 L8 11 L13 6 Z";
  return (
    <svg className="h-4 w-4" viewBox="0 0 16 16" fill="currentColor">
      <path d={d} />
    </svg>
  );
}

/**
 * Searchable dropdown for selecting a GitHub repository.
 * Renders the option list in a portal above the input to avoid
 * parent overflow clipping.
 */
export default function RepoSearchDropdown({ repos, selectedRepo, onSelect, disabled }: Props) {
  const [query, setQuery] = useState(selectedRepo);
  const [open, setOpen] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [style, setStyle] = useState<{ bottom: number; left: number; width: number } | null>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return repos;
    return repos.filter((r) => r.full_name.toLowerCase().includes(q));
  }, [repos, query]);

  const close = useCallback(() => setOpen(false), []);

  // Keep the display text in sync with external selection changes
  useEffect(() => {
    setQuery(selectedRepo);
  }, [selectedRepo]);

  // Position the dropdown above the input
  useLayoutEffect(() => {
    if (open && inputRef.current) {
      const rect = inputRef.current.getBoundingClientRect();
      setStyle({
        bottom: window.innerHeight - rect.top + 4,
        left: rect.left,
        width: rect.width,
      });
    } else {
      setStyle(null);
    }
  }, [open]);

  // Close on outside click or external scroll
  useEffect(() => {
    if (!open) return;

    function handleClickOutside(e: MouseEvent) {
      const target = e.target as Node;
      if (inputRef.current?.contains(target) || dropdownRef.current?.contains(target)) return;
      close();
    }

    function handleScroll(e: Event) {
      if (dropdownRef.current?.contains(e.target as Node)) return;
      close();
    }

    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("scroll", handleScroll, true);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("scroll", handleScroll, true);
    };
  }, [open, close]);

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={open ? query : selectedRepo || ""}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder="Select a repository..."
        className="h-12 w-full rounded border border-zinc-300 bg-zinc-50 px-4 py-3 pr-10 text-sm text-zinc-700 placeholder:text-zinc-400"
        disabled={disabled}
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label="Search repositories"
      />

      <span
        className="absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer text-zinc-500"
        onClick={() => inputRef.current?.focus()}
        role="button"
        aria-label={open ? "Close repository list" : "Open repository list"}
      >
        <ChevronIcon direction={open ? "down" : "up"} />
      </span>

      {open &&
        style &&
        createPortal(
          <div
            ref={dropdownRef}
            className="fixed z-[9999] max-h-48 overflow-y-auto rounded border border-zinc-300 bg-white shadow-lg"
            role="listbox"
            style={{ bottom: style.bottom, left: style.left, width: style.width }}
          >
            {filtered.length === 0 ? (
              <div className="px-4 py-3 text-sm text-zinc-500">No matching repositories</div>
            ) : (
              filtered.map((repo) => (
                <button
                  key={repo.full_name}
                  type="button"
                  role="option"
                  aria-selected={selectedRepo === repo.full_name}
                  className={`block w-full px-4 py-2.5 text-left text-sm hover:bg-zinc-100 ${
                    selectedRepo === repo.full_name ? "bg-zinc-100 font-medium" : "text-zinc-700"
                  }`}
                  onClick={() => {
                    onSelect(repo.full_name);
                    setQuery(repo.full_name);
                    setOpen(false);
                  }}
                >
                  {repo.full_name}
                </button>
              ))
            )}
          </div>,
          document.body,
        )}
    </div>
  );
}
