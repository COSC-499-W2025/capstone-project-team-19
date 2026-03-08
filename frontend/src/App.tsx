import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import type { ReactNode } from "react";

import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";
import HomePage from "./pages/Home";
import { tokenStore } from "./auth/token";
import UploadPage from "./pages/Upload";
import ProjectsPage from "./pages/Projects";
import InsightsPage from "./pages/Insights";
import OutputsPage from "./pages/Outputs";

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
              <Navigate to="/upload/consent" replace />
            </RequireAuth>
          }
        />

        <Route
          path="/upload/consent"
          element={
            <RequireAuth>
              <UploadPage />
            </RequireAuth>
          }
        />

        <Route
          path="/upload/upload"
          element={
            <RequireAuth>
              <UploadPage />
            </RequireAuth>
          }
        />

        <Route
          path="/projects"
          element={
            <RequireAuth>
              <ProjectsPage />
            </RequireAuth>
          }
        />

        <Route
          path="/insights"
          element={
            <RequireAuth>
              <InsightsPage />
            </RequireAuth>
          }
        />

        <Route
          path="/outputs"
          element={
            <RequireAuth>
              <OutputsPage />
            </RequireAuth>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
