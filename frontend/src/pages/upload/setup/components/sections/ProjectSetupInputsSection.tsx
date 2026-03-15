type Props = {
  collaborative: boolean;
};

export default function ProjectSetupInputsSection({ collaborative }: Props) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white px-3 py-2">
      <h4 className="mb-1 text-sm leading-tight font-semibold text-zinc-900">Project Setup Inputs</h4>
      <p className="m-0 text-xs leading-relaxed text-zinc-700">
        {collaborative
          ? "File roles, identity choices, and integrations are scaffolded next."
          : "File roles, key role, and integrations are scaffolded next."}
      </p>
    </div>
  );
}
