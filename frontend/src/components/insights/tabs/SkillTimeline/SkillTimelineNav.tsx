import "./SkillTimeline.css";

type SkillTimelineSection = "timeline" | "totals" | "undated";

export default function SkillTimelineNav({activeSection, setActiveSection}: {
    activeSection: SkillTimelineSection;
    setActiveSection: (s: SkillTimelineSection) => void;
}) {
    return (
        <nav className="skill-timeline-nav">
            <button className={activeSection === "timeline" ? "active" : ""} onClick={() => setActiveSection("timeline")}>Timeline</button>
            <button className={activeSection === "totals" ? "active" : ""} onClick={() => setActiveSection("totals")}>Current Totals</button>
            <button className={activeSection === "undated" ? "active" : ""} onClick={() => setActiveSection("undated")}>Undated Skills</button>
        </nav>
    );
}