import TopBar from "../components/TopBar";
import { getUsername } from "../auth/user";
import InsightsLayout from "../components/insights/InsightsLayout";
import { PageContainer, PageHeader, SectionCard } from "../components/shared";

export default function InsightsPage() {
  const username = getUsername();

  return (
    <>
      <TopBar showNav username={username} />

      <PageContainer className="min-h-[calc(100vh-56px)] bg-background pt-[12px]">
        <PageHeader
          title="Insights"
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "Insights" },
          ]}
        />

        <SectionCard className="w-full overflow-hidden !p-0 bg-white">
          <InsightsLayout />
        </SectionCard>
      </PageContainer>
    </>
  );
}