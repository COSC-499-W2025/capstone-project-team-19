import TopBar from "../components/TopBar";
import { tokenStore } from "../auth/token";
import { getUsernameFromToken } from "../auth/jwt";

export default function Placeholder({ title }: { title: string }) {
  const username = getUsernameFromToken(tokenStore.get()) ?? "user";

  return (
    <>
      <TopBar showNav username={username} />
      <div style={{ padding: 24 }}>{title} (placeholder)</div>
    </>
  );
}