import { useEffect, useState } from "react";

export default function ScoreInfoTooltip({ inline }: { inline?: boolean }) {
    const [open, setOpen] = useState(false);

    useEffect(() => {
        if (open) {
            document.body.style.overflow = "hidden";
        }
        return () => {
            document.body.style.overflow = "";
        };
    }, [open]);

    return (
        <>
            <button type="button" className={`rounded-full w-[18px] h-[18px] p-0 flex items-center justify-center text-xs border border-slate-700 bg-transparent cursor-pointer hover:bg-black/5 shrink-0 ${inline ? "" : "absolute right-4 top-1/2 -translate-y-1/2"}`} onClick={() => setOpen(true)} aria-label="How are skill scores calculated?" title="How are skill scores calculated?">?</button>
            {open && (
                <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-[1000] p-6" onClick={() => setOpen(false)} role="dialog" aria-modal="true" aria-labelledby="score-info-title">
                    <div className="bg-white rounded-[10px] shadow-[0_20px_50px_rgba(0,0,0,0.25)] max-w-[440px] w-full max-h-[90vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-between items-start gap-3 mb-2.5 border-b-2 border-slate-900">
                            <h2 id="score-info-title" className="m-0 text-lg font-bold text-slate-900">How skill scores work</h2>
                            <button type="button" className={`inline-flex rounded-full w-[18px] h-[18px] p-0 items-center justify-center align-middle text-xs leading-none border border-slate-700 bg-transparent cursor-pointer hover:bg-black/5 shrink-0 ${inline ? "" : "absolute right-4 top-1/2 -translate-y-1/2"}`} onClick={() => setOpen(false)} aria-label="Close">×</button>
                        </div>
                        <p className="m-0 mb-4 text-sm leading-relaxed text-justify text-slate-700">
                            Skill scores are calculated from the analysis of your projects' content.
                            Each time a skill is detected in a project, it contributes to that skill's total score.
                        </p>
                        <ul className="m-0 mb-5 pl-5 pr-5 text-sm leading-snug text-justify text-slate-700 [&>li]:mb-4 last:[&>li]:mb-0 [&_strong]:text-slate-900">
                            <li>
                                <strong>Source:</strong> Each project where a skill appears contributes a score to that skill (based on our skill detection and classification).
                            </li>
                            <li>
                                <strong>Combining contributions:</strong> We use a diminishing-returns
                                formula so that more evidence still raises the total, but each extra
                                contribution adds a bit less. That keeps the scale meaningful and
                                bounded between 0 and 1.
                            </li>
                            <li>
                                <strong>Dated and undated:</strong> Current totals include both
                                dated activity (with known project dates) and undated activity, so
                                you see one combined score per skill.
                            </li>
                            <li>
                                <strong>Level indicators:</strong> On the Timeline and Skills Log, skill
                                levels appear as stars: 1 star = Beginner, 2 stars = Intermediate, 3 stars = Advanced.
                            </li>
                            <li>
                                <strong>See the breakdown:</strong> On the Skills Overview tab, hover
                                over a skill's bar to see which projects contributed to that skill.
                            </li>
                        </ul>
                    </div>
                </div>
            )}
        </>
    );
}
