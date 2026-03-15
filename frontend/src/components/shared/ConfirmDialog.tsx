import AppButton from "./AppButton";
import AppDialogShell from "./AppDialogShell";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  onConfirm: () => void;
};

export default function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Confirm",
  onConfirm,
}: Props) {
  return (
    <AppDialogShell
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      description={description}
      width="sm"
      footer={
        <>
          <AppButton variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </AppButton>
          <AppButton
            variant="destructive"
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
      <div className="rounded-xl border border-destructive/15 bg-destructive/5 px-4 py-3 text-sm text-foreground">
        This action cannot be undone.
      </div>
    </AppDialogShell>
  );
}