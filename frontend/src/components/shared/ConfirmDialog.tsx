import AppButton from "./AppButton";
import AppDialogShell from "./AppDialogShell";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description: string;
  confirmLabel?: string;
  onConfirm: () => void;
};

export default function ConfirmDialog({
  open,
  onOpenChange,
  title = "Confirm",
  description,
  confirmLabel = "Ok",
  onConfirm,
}: Props) {
  return (
    <AppDialogShell
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      width="md"
      bodyClassName="px-0 py-0"
      footer={
        <>
          <AppButton variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </AppButton>
          <AppButton
            onClick={() => {
              onConfirm();
              onOpenChange(false);
            }}
          >
            {confirmLabel}
          </AppButton>
        </>
      }
    >
      <div className="border-y border-[#ececec] px-[12px] py-[14px] text-center text-[14px] leading-[1.4] text-[#3f3f3f]">
        {description}
      </div>
    </AppDialogShell>
  );
}