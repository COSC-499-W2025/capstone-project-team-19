import AppButton from "./AppButton";
import AppDialogShell from "./AppDialogShell";
import AppSelect from "./AppSelect";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export default function DurationDialog({ open, onOpenChange }: Props) {
  return (
    <AppDialogShell
      open={open}
      onOpenChange={onOpenChange}
      title="Duration"
      width="md"
      footer={
        <>
          <AppButton variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </AppButton>
          <AppButton onClick={() => onOpenChange(false)}>Save</AppButton>
        </>
      }
    >
      <div className="grid grid-cols-2 gap-[16px]">
        <div className="space-y-[6px]">
          <div className="text-[14px] font-medium text-foreground">Start Date</div>
          <div className="flex gap-[8px]">
            <AppSelect className="w-[96px]">
              <option>Month</option>
            </AppSelect>
            <AppSelect className="w-[76px]">
              <option>Year</option>
            </AppSelect>
          </div>
        </div>

        <div className="space-y-[6px]">
          <div className="text-[14px] font-medium text-foreground">End Date</div>
          <div className="flex gap-[8px]">
            <AppSelect className="w-[96px]">
              <option>Month</option>
            </AppSelect>
            <AppSelect className="w-[76px]">
              <option>Year</option>
            </AppSelect>
          </div>
        </div>
      </div>
    </AppDialogShell>
  );
}