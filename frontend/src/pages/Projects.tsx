import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";

export default function ProjectsPage() {
  const username = getUsername();

  return (
    <>
      <TopBar showNav username={username} />
      <div className="content">
        <h2>Projects</h2>

        {/* TODO: list projects, ranking, etc */}
        <div className="cardWide">
          <p>Projects list UI goes here.</p>
        </div>
      </div>
    </>
  );
}