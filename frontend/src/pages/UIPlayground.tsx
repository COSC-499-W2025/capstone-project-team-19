import { useState } from "react";
import TopBar from "../components/TopBar";
import {
  AppButton,
  AppField,
  AppInput,
  AppRadio,
  AppSelect,
  AppTextarea,
  ConfirmDialog,
  ContactDialog,
  ContributionBulletsDialog,
  CreateResumeDialog,
  DurationDialog,
  FeatureTile,
  OverflowMenu,
  PageContainer,
  PageHeader,
  SectionCard,
  SectionTabs,
  TagPill,
} from "../components/shared";
import {
  BriefcaseBusiness,
  FileText,
  Pencil,
  Trash2,
  Upload,
} from "../lib/ui-icons";

export default function UIPlaygroundPage() {
  const [tab, setTab] = useState("summary");

  const [createResumeOpen, setCreateResumeOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [contactOpen, setContactOpen] = useState(false);
  const [contributionOpen, setContributionOpen] = useState(false);
  const [durationOpen, setDurationOpen] = useState(false);

  return (
    <>
      <TopBar showNav username="ui-preview" />

      <PageContainer className="flex flex-col gap-[18px]">
        <PageHeader
          title="UI Preview"
          subtitle="Internal preview for the redesigned baseline components."
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "UI Preview" },
          ]}
        />

        <SectionCard className="space-y-[14px]">
          <div className="logoText text-[20px] text-primary">resuMe</div>

          <div>
            <div className="text-[16px] font-bold text-foreground">Typography</div>
            <div className="mt-[4px] text-[10px] text-[#7f7f7f]">
              Roboto light / regular / medium / bold, and Open Sans Bold for the logo only.
            </div>
          </div>

          <div className="space-y-[4px]">
            <div className="text-[16px] font-bold">Page title example</div>
            <div className="text-[12px] font-medium">Section heading example</div>
            <div className="text-[11px] font-normal">Body text example</div>
            <div className="text-[10px] font-light text-[#7f7f7f]">Muted/helper text example</div>
          </div>
        </SectionCard>

        <SectionCard className="space-y-[14px]">
          <div className="text-[12px] font-medium">Buttons</div>

          <div className="flex flex-wrap gap-[8px]">
            <AppButton>Primary</AppButton>
            <AppButton variant="outline">Outline</AppButton>
            <AppButton variant="ghost">Ghost</AppButton>
            <AppButton variant="destructive">Delete</AppButton>
            <AppButton size="icon" aria-label="Edit">
              <Pencil className="h-[11px] w-[11px]" strokeWidth={1.6} />
            </AppButton>
          </div>
        </SectionCard>

        <SectionCard className="space-y-[14px]">
          <div className="text-[12px] font-medium">Fields</div>

          <div className="grid gap-[10px] md:grid-cols-2">
            <AppField label="Resume Name">
              <AppInput placeholder="resume1" />
            </AppField>

            <AppField label="Project Type">
              <AppSelect defaultValue="">
                <option value="" disabled>
                  Select one
                </option>
                <option value="individual">Individual</option>
                <option value="collaborative">Collaborative</option>
              </AppSelect>
            </AppField>

            <div className="md:col-span-2">
              <AppField label="Contribution Bullets">
                <AppTextarea placeholder="Write a few bullets..." />
              </AppField>
            </div>
          </div>
        </SectionCard>

        <SectionCard className="space-y-[14px]">
          <div className="text-[12px] font-medium">Radio buttons</div>

          <div className="flex flex-col gap-[8px]">
            <AppRadio name="consent-demo" label="Yes, I consent." />
            <AppRadio name="consent-demo" label="No, I do not consent." />
          </div>
        </SectionCard>

        <SectionCard className="space-y-[14px]">
          <div className="text-[12px] font-medium">Pills</div>

          <div className="flex flex-wrap gap-[8px]">
            <TagPill>Code</TagPill>
            <TagPill>Individual</TagPill>
          </div>
        </SectionCard>

        <SectionCard className="space-y-[14px]">
          <div className="text-[12px] font-medium">Outputs tiles</div>

          <div className="flex gap-[16px]">
            <FeatureTile title="My Resumes" icon={FileText} />
            <FeatureTile title="My Portfolio" icon={BriefcaseBusiness} />
          </div>
        </SectionCard>

        <SectionCard className="space-y-[14px]">
          <div className="text-[12px] font-medium">Blue underline tabs</div>

          <SectionTabs
            tabs={[
              { key: "summary", label: "Summary" },
              { key: "feedback", label: "Feedback" },
            ]}
            activeKey={tab}
            onChange={setTab}
          />
        </SectionCard>

        <SectionCard className="space-y-[14px]">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-[12px] font-medium">Three-dot overflow menu</div>
              <div className="mt-[2px] text-[10px] text-[#7f7f7f]">
                Use this for thumbnail/settings menus like in the project page screenshot.
              </div>
            </div>

            <OverflowMenu
              items={[
                { label: "Change Thumbnail", onClick: () => {} },
                { label: "Remove Thumbnail", onClick: () => {} },
              ]}
            />
          </div>
        </SectionCard>

        <SectionCard className="space-y-[14px]">
          <div className="text-[12px] font-medium">Icon usage</div>

          <div className="flex flex-wrap gap-[8px] text-[10px] text-[#6d6d6d]">
            <div className="flex items-center gap-[6px] border border-[#e5e5e5] px-[8px] py-[6px]">
              <Upload className="h-[11px] w-[11px]" strokeWidth={1.6} />
              Upload
            </div>
            <div className="flex items-center gap-[6px] border border-[#e5e5e5] px-[8px] py-[6px]">
              <FileText className="h-[11px] w-[11px]" strokeWidth={1.6} />
              Resume
            </div>
            <div className="flex items-center gap-[6px] border border-[#e5e5e5] px-[8px] py-[6px]">
              <Trash2 className="h-[11px] w-[11px]" strokeWidth={1.6} />
              Delete
            </div>
          </div>
        </SectionCard>

        <SectionCard className="space-y-[14px]">
          <div className="text-[12px] font-medium">All popup patterns</div>

          <div className="flex flex-wrap gap-[8px]">
            <AppButton onClick={() => setCreateResumeOpen(true)}>
              Create Resume
            </AppButton>
            <AppButton variant="outline" onClick={() => setContactOpen(true)}>
              Contact
            </AppButton>
            <AppButton variant="outline" onClick={() => setContributionOpen(true)}>
              Contribution Bullets
            </AppButton>
            <AppButton variant="outline" onClick={() => setDurationOpen(true)}>
              Duration
            </AppButton>
            <AppButton variant="destructive" onClick={() => setConfirmOpen(true)}>
              Delete Confirm
            </AppButton>
          </div>
        </SectionCard>
      </PageContainer>

      <CreateResumeDialog
        open={createResumeOpen}
        onOpenChange={setCreateResumeOpen}
      />

      <ContactDialog open={contactOpen} onOpenChange={setContactOpen} />

      <ContributionBulletsDialog
        open={contributionOpen}
        onOpenChange={setContributionOpen}
      />

      <DurationDialog open={durationOpen} onOpenChange={setDurationOpen} />

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        description="Are you sure you want to delete this resume?"
        confirmLabel="Ok"
        onConfirm={() => {}}
      />
    </>
  );
}