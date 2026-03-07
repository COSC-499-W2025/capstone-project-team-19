import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";

export default function UploadPage() {
  const username = getUsername();

  return (
    <>
      <TopBar showNav username={username} />
      <div className="content">
        <h2>Upload</h2>

        {/* TODO: connect to upload wizard endpoints */}
        <div className="cardWide">
          <p>Upload flow UI goes here.</p>
        </div>
      </div>
    </>
  );
}