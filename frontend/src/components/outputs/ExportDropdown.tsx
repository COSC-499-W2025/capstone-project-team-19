import { useState, useRef, useEffect } from "react";

type Props = {
  onDocx: () => void;
  onPdf: () => void;
  disabled?: boolean;
};

export default function ExportDropdown({ onDocx, onPdf, disabled = false }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div className="exportDropdown" ref={ref}>
      <button
        className="actionBtn dark"
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        title={disabled ? "Resume must fit on one page before export" : undefined}
      >
        Export
      </button>
      {open && (
        <div className="exportMenu">
          <button
            className="exportMenuItem"
            onClick={() => { onDocx(); setOpen(false); }}
            disabled={disabled}
          >
            Export as DOCX
          </button>
          <button
            className="exportMenuItem"
            onClick={() => { onPdf(); setOpen(false); }}
            disabled={disabled}
          >
            Export as PDF
          </button>
        </div>
      )}
    </div>
  );
}
