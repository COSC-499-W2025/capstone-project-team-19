import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";
import { tokenStore } from "./auth/token";
import type { ReactNode } from "react";

function Home() {
  return <div style={{ padding: 24 }}>Home (placeholder)</div>;
}

function RequireAuth({ children }: { children: ReactNode }) {
  const token = tokenStore.get();
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <Home />
            </RequireAuth>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}