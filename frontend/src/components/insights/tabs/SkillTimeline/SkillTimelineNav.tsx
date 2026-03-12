type SkillTimelineSection = "timeline" | "totals" | "undated";

const navButton = (active: boolean) =>
    active
        ? "bg-white text-black border-2 border-black rounded-t-lg rounded-br-none border-r-0 mr-[-11.5px] pr-[21.5px]"
        : "bg-black text-white border-2 border-black rounded-lg";

export default function SkillTimelineNav({activeSection, setActiveSection}: {
    activeSection: SkillTimelineSection;
    setActiveSection: (s: SkillTimelineSection) => void;
}) {
    return (
        <nav className="flex flex-col flex-shrink-0 gap-1.5 w-[150px] pr-2.5 border-r-2 border-black">
            <button
                className={`py-2.5 px-2.5 ${navButton(activeSection === "timeline")}`}
                onClick={() => setActiveSection("timeline")}
            >
                Timeline
            </button>
            <button
                className={`py-2.5 px-2.5 ${navButton(activeSection === "totals")}`}
                onClick={() => setActiveSection("totals")}
            >
                Current Totals
            </button>
            <button
                className={`py-2.5 px-2.5 ${navButton(activeSection === "undated")}`}
                onClick={() => setActiveSection("undated")}
            >
                Undated Skills
            </button>
        </nav>
    );
}