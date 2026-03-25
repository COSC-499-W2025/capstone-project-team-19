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
  const [view, setView] = useState<View>({ kind: "resumes" });
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

  const goResumes = () => setView({ kind: "resumes" });

  const headerConfig =
    view.kind === "resumes"
      ? {
          title: "Resume",
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Resume" },
          ],
        }
      : view.kind === "resume-detail"
      ? {
          title: "Resume Detail",
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Resume", onClick: goResumes },
            { label: "Resume Detail" },
          ],
        }
      : {
          title: "Resume",
          breadcrumbs: [
            { label: "Home", href: "/" },
            { label: "Resume" },
          ],
        };

  return (
    <>
      <TopBar showNav username={username} />

      <PageContainer className="flex min-h-[calc(100vh-56px)] flex-col bg-background pt-[12px]">
        <PageHeader title={headerConfig.title} breadcrumbs={headerConfig.breadcrumbs} />
        <SectionCard className="flex w-full flex-1 flex-col bg-white">
          {renderView()}
        </SectionCard>
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