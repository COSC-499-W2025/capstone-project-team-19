type Props = {
  onSelect: (view: "resumes" | "portfolio") => void;
};

export default function OutputsLanding({ onSelect }: Props) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-12 px-6 py-16">
      <button className="outputCard" onClick={() => onSelect("resumes")}>
        <div className="outputCardIcon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#555" strokeWidth="1.5">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
        </div>
        <span className="outputCardLabel">Resume Items</span>
      </button>

      <button className="outputCard" onClick={() => onSelect("portfolio")}>
        <div className="outputCardIcon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#555" strokeWidth="1.5">
            <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
            <path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
          </svg>
        </div>
        <span className="outputCardLabel">Portfolio Items</span>
      </button>
    </div>
  );
}