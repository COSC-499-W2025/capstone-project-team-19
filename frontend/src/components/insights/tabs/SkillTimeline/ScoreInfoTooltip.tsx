import { useEffect, useState } from "react";

export default function ScoreInfoTooltip() {
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
            <button
                type="button"
                className="score-info-trigger"
                onClick={() => setOpen(true)}
                aria-label="How are skill scores calculated?"
                title="How are skill scores calculated?"
            >
                ?
            </button>

            {open && (
                <div
                    className="score-info-overlay"
                    onClick={() => setOpen(false)}
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="score-info-title"
                >
                    <div className="score-info-popup" onClick={(e) => e.stopPropagation()}>
                        <div className="score-info-popup-header">
                            <h2 id="score-info-title" className="score-info-popup-title">
                                How skill scores work
                            </h2>
                            <button
                                type="button"
                                className="score-info-popup-close"
                                onClick={() => setOpen(false)}
                                aria-label="Close"
                            >
                                ×
                            </button>
                        </div>
                        <p className="score-info-popup-intro">
                            Skill scores are calculated from the analysis of your projects’ content.
                            Each time a skill is detected in a project, it contributes to that skill’s total score.                        </p>
                        <br/>
                        <ul className="score-info-popup-list">
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
                                <strong>See the breakdown:</strong> On the Current Totals tab, hover
                                over a skill’s bar to see which projects contributed to that skill.
                            </li>
                        </ul>
                    </div>
                </div>
            )}
        </>
    );
}
