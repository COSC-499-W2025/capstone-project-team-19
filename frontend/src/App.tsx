import {
  createBrowserRouter,
  createRoutesFromElements,
  Navigate,
  Route,
  RouterProvider,
  useParams,
} from "react-router-dom";

import { createAppRouter } from "./router";

export default function App() {
  const router = createAppRouter();
  return <RouterProvider router={router} />;
}

function createAppRouter() {
  return createBrowserRouter(
    createRoutesFromElements(
    <>
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
        path="/resume"
        element={
          <RequireAuth>
            <OutputsPage />
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

      <Route path="/public/:username" element={<PublicHomeRedirect />} />
      <Route path="/public/:username/projects" element={<PublicProjectsPage />} />
      <Route path="/public/:username/projects/:id" element={<PublicProjectDetailPage />} />
      <Route path="/public/:username/insights" element={<PublicInsightsPage />} />
      <Route path="/public/:username/resume" element={<PublicOutputsPage />} />
      <Route path="/public/:username/outputs" element={<PublicOutputsPage />} />

      <Route
        path="/ui-preview"
        element={
          <RequireAuth>
            <UIPlaygroundPage />
          </RequireAuth>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </>
  )
  );
}
