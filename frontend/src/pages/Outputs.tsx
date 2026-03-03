import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";

export default function OutputsPage() {
  const username = getUsername();

  return (
    <>
      <TopBar showNav username={username} />
      <div className="content">
        <h2>Outputs</h2>

        {/* TODO: export resume/portfolio, download docs */}
        <div className="cardWide">
          <p>Outputs UI goes here.</p>
        </div>
      </div>
    </>
  );
}