import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import type { ReactNode } from "react";

import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";
import HomePage from "./pages/Home";
import Placeholder from "./pages/Placeholder";
import { tokenStore } from "./auth/token";

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
              <HomePage />
            </RequireAuth>
          }
        />

        <Route
          path="/upload"
          element={
            <RequireAuth>
              <Placeholder title="Upload" />
            </RequireAuth>
          }
        />
        <Route
          path="/projects"
          element={
            <RequireAuth>
              <Placeholder title="Projects" />
            </RequireAuth>
          }
        />
        <Route
          path="/insights"
          element={
            <RequireAuth>
              <Placeholder title="Insights" />
            </RequireAuth>
          }
        />
        <Route
          path="/outputs"
          element={
            <RequireAuth>
              <Placeholder title="Outputs" />
            </RequireAuth>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}