import { createBrowserRouter, Navigate, RouterProvider, useParams } from "react-router-dom";
import type { ReactNode } from "react";

import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";
import HomePage from "./pages/Home";
import { tokenStore, isTokenValid } from "./auth/token";
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
import PublicInsightsPage from "./pages/public/PublicInsightsPage";
import PublicOutputsPage from "./pages/public/PublicOutputsPage";

function PublicHomeRedirect() {
  const { username } = useParams<{ username: string }>();
  return <Navigate to={`/public/${username}/projects`} replace />;
}

function RequireAuth({ children }: { children: ReactNode }) {
  const token = tokenStore.get();

  if (!isTokenValid(token)) {
    tokenStore.clear();
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/", element: <RequireAuth><HomePage /></RequireAuth> },
  { path: "/upload", element: <RequireAuth><Navigate to="/upload/consent" replace /></RequireAuth> },
  { path: "/upload/consent", element: <RequireAuth><ConsentPage /></RequireAuth> },
  { path: "/upload/upload", element: <RequireAuth><UploadPage /></RequireAuth> },
  { path: "/upload/setup", element: <RequireAuth><UploadSetupPage /></RequireAuth> },
  { path: "/upload/analyze", element: <RequireAuth><UploadAnalyzePage /></RequireAuth> },
  { path: "/projects", element: <RequireAuth><ProjectsPage /></RequireAuth> },
  { path: "/projects/:id", element: <RequireAuth><ProjectDetailPage /></RequireAuth> },
  { path: "/insights", element: <RequireAuth><InsightsPage /></RequireAuth> },
  { path: "/resume", element: <RequireAuth><OutputsPage /></RequireAuth> },
  { path: "/profile", element: <RequireAuth><ProfilePage /></RequireAuth> },
  { path: "/public/:username", element: <PublicHomeRedirect /> },
  { path: "/public/:username/projects", element: <PublicProjectsPage /> },
  { path: "/public/:username/projects/:id", element: <PublicProjectDetailPage /> },
  { path: "/public/:username/insights", element: <PublicInsightsPage /> },
  { path: "/public/:username/resume", element: <PublicOutputsPage /> },
  { path: "/ui-preview", element: <RequireAuth><UIPlaygroundPage /></RequireAuth> },
  { path: "*", element: <Navigate to="/" replace /> },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
