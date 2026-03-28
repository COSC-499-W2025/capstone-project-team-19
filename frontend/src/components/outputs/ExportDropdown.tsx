import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

type Props = {
  onDocx: () => void;
  onPdf: () => void;
};

export default function ExportDropdown({ onDocx, onPdf }: Props) {
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
    <div className="relative" ref={ref}>
      <Button variant="outline" size="sm" onClick={() => setOpen(!open)} className="gap-1.5">
        <Download className="size-3.5" />
        Export
      </Button>
      {open && (
        <div className="absolute right-0 z-20 mt-1 min-w-[160px] rounded-md border border-[#e5e5e5] bg-white py-1 shadow-md">
          <button
            className="w-full cursor-pointer px-3 py-1.5 text-left text-sm text-slate-700 hover:bg-slate-50"
            onClick={() => { onDocx(); setOpen(false); }}
          >
            Export as DOCX
          </button>
          <button
            className="w-full cursor-pointer px-3 py-1.5 text-left text-sm text-slate-700 hover:bg-slate-50"
            onClick={() => { onPdf(); setOpen(false); }}
          >
            Export as PDF
          </button>
        </div>
      )}
    </div>
  );
}
