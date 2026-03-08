import { useNavigate } from "react-router-dom";
import TopBar from "../components/TopBar";
import { tokenStore } from "../auth/token";
import { getUsernameFromToken } from "../auth/jwt";

export default function HomePage() {
  const nav = useNavigate();
  const username = getUsernameFromToken(tokenStore.get()) ?? "user";

  return (
    <>
      <TopBar showNav username={username} />

      <div className="home">
        <div className="hero">
          <div className="heroTitle">Hello, {username}!</div>
          <div className="heroSubtitle">Welcome aboard! Let&apos;s turn your work into cool insights.</div>

          <button className="primaryBtn" onClick={() => nav("/upload/consent")}>
            Start analyzing
          </button>
        </div>
      </div>
    </>
  );
}
