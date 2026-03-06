import { useEffect, useState } from "react";
import { api } from "./api/client";

export default function App() {
  const [msg, setMsg] = useState("Loading...");

  useEffect(() => {
    api
      .get<{ status: string }>("/health")
      .then((r) => setMsg(r.status))
      .catch((e) => setMsg(String(e)));
  }, []);

  return <div style={{ padding: 24 }}>Backend says: {msg}</div>;
}