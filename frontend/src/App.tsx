import { BrowserRouter, Routes, Route, Navigate, useParams } from "react-router-dom";

function PublicHomeRedirect() {
  const { username } = useParams<{ username: string }>();
  return <Navigate to={`/public/${username}/projects`} replace />;
}
import type { ReactNode } from "react";

import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";
import HomePage from "./pages/Home";
import { tokenStore } from "./auth/token";
import UploadPage from "./pages/upload/upload/UploadPage";
import UploadSetupPage from "./pages/upload/setup/SetupPage";
import UploadAnalyzePage from "./pages/upload/analyze/AnalyzePage";
import ConsentPage from "./pages/upload/consent/ConsentPage";
import ProjectsPage from "./pages/Projects";
import ProjectDetailPage from "./pages/ProjectDetail";
import InsightsPage from "./pages/InsightsPage";
import OutputsPage from "./pages/Outputs";
import ProfilePage from "./pages/Profile";
import UIPlaygroundPage from "./pages/UIPlayground";
import PublicProjectsPage from "./pages/public/PublicProjects";
import PublicProjectDetailPage from "./pages/public/PublicProjectDetail";

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
              <ConsentPage />
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
          path="/upload/setup"
          element={
            <RequireAuth>
              <UploadSetupPage />
            </RequireAuth>
          }
        />

        <Route
          path="/upload/analyze"
          element={
            <RequireAuth>
              <UploadAnalyzePage />
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
          path="/projects/:id"
          element={
            <RequireAuth>
              <ProjectDetailPage />
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

        <Route
          path="/profile"
          element={
            <RequireAuth>
              <ProfilePage />
            </RequireAuth>
          }
        />

        {/* Public routes — no auth required */}
        <Route path="/public/:username" element={<PublicHomeRedirect />} />
        <Route path="/public/:username/projects" element={<PublicProjectsPage />} />
        <Route path="/public/:username/projects/:id" element={<PublicProjectDetailPage />} />

        <Route
          path="/ui-preview"
          element={
            <RequireAuth>
              <UIPlaygroundPage />
            </RequireAuth>
          }
        />
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
