import { useState } from "react";
import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";
import OutputsLanding from "../components/outputs/OutputsLanding";
import ResumeList from "../components/outputs/ResumeList";
import ResumeDetail from "../components/outputs/ResumeDetail";
import CreateResumeModal from "../components/outputs/CreateResumeModal";
import PortfolioView from "../components/outputs/PortfolioView";
import { PageContainer, PageHeader, SectionCard } from "../components/shared";

type View =
  | { kind: "landing" }
  | { kind: "resumes" }
  | { kind: "resume-detail"; id: number; editing?: boolean }
  | { kind: "portfolio" };

export default function OutputsPage() {
  const username = getUsername();
  const [view, setView] = useState<View>({ kind: "landing" });
  const [showCreate, setShowCreate] = useState(false);

  function renderView() {
    switch (view.kind) {
      case "landing":
        return (
          <OutputsLanding
            onSelect={(v) =>
              setView(v === "resumes" ? { kind: "resumes" } : { kind: "portfolio" })
            }
          />
        );
      case "resumes":
        return (
          <ResumeList
            onBack={() => setView({ kind: "landing" })}
            onView={(id) => setView({ kind: "resume-detail", id })}
            onEdit={(id) => setView({ kind: "resume-detail", id, editing: true })}
            onCreateNew={() => setShowCreate(true)}
          />
        );
      case "resume-detail":
        return (
          <ResumeDetail
            resumeId={view.id}
            initialEditing={view.editing}
            onBack={() => setView({ kind: "resumes" })}
          />
        );
      case "portfolio":
        return <PortfolioView onBack={() => setView({ kind: "landing" })} />;
    }
  }

  const goLanding = () => setView({ kind: "landing" });
  const goResumes = () => setView({ kind: "resumes" });

  const headerConfig =
    view.kind === "landing"
      ? {
          title: "Outputs",
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Outputs" },
          ],
        }
      : view.kind === "resumes"
      ? {
          title: "Resume Items",
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Outputs", onClick: goLanding },
            { label: "Resume Items" },
          ],
        }
      : view.kind === "resume-detail"
      ? {
          title: "Resume Detail",
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Outputs", onClick: goLanding },
            { label: "Resume Items", onClick: goResumes },
            { label: "Resume Detail" },
          ],
        }
      : {
          title: "Portfolio Items",
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Outputs", onClick: goLanding },
            { label: "Portfolio Items" },
          ],
        };

  return (
    <>
      <TopBar showNav username={username} />

      <PageContainer className="min-h-[calc(100vh-56px)] bg-background pt-[12px]">
        <PageHeader title={headerConfig.title} breadcrumbs={headerConfig.breadcrumbs} />
        <SectionCard className="w-full bg-white">{renderView()}</SectionCard>
      </PageContainer>

      {showCreate && (
        <CreateResumeModal
          onClose={() => setShowCreate(false)}
          onCreated={(id) => {
            setShowCreate(false);
            setView({ kind: "resume-detail", id });
          }}
        />
      )}
    </>
  );
}