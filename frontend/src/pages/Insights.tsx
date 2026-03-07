import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";

export default function InsightsPage() {
  const username = getUsername();

  return (
    <>
      <TopBar showNav username={username} />
      <div className="content">
        <h2>Insights</h2>

        {/* TODO: show skill timeline, heatmap, summaries */}
        <div className="cardWide">
          <p>Insights UI goes here.</p>
        </div>
      </div>
    </>
  );
}