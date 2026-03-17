import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";
import InsightsLayout from "../components/insights/InsightsLayout";
import { PageContainer, PageHeader, SectionCard } from "../components/shared";

export default function InsightsPage() {
  const username = getUsername();

  return (
    <>
      <TopBar showNav username={username} />

      <div className="min-h-[calc(100vh-56px)] bg-background">
        <PageContainer className="pt-[12px]">
          <PageHeader
            title="Insights"
            breadcrumbs={[
              { label: "Home", href: "/" },
              { label: "Insights" },
            ]}
          />

          <SectionCard className="w-full max-w-[1110px] self-center overflow-hidden !p-0 bg-white">
            <InsightsLayout />
          </SectionCard>
        </PageContainer>
      </div>
    </>
  );
}