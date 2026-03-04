export default function InsightsSubNav({ activeTab, onChange }: any) {
    return (
        <div className="insights-subnav">
            <button className={`insights-tab ${activeTab === "ranked-projects" ? "active" : ""}`} onClick={() => onChange("ranked-projects")}>Ranked Projects</button>
            <button className={`insights-tab ${activeTab === "skill-timeline" ? "active" : ""}`} onClick={() => onChange("skill-timeline")}>Skill Timeline</button>
            <button className={`insights-tab ${activeTab === "chronological-skills" ? "active" : ""}`} onClick={() => onChange("chronological-skills")}>Chronological Skills</button>
            <button className={`insights-tab ${activeTab === "activity-heatmap" ? "active" : ""}`} onClick={() => onChange("activity-heatmap")}>Activity Heatmap</button>
        </div>
    );
}