type Props = {
  collaborative: boolean;
};

export default function ProjectSetupInputsSection({ collaborative }: Props) {
  return (
    <div className="setupPlaceholderBlock">
      <h4>Project Setup Inputs</h4>
      <p>
        {collaborative
          ? "File roles, identity choices, and integrations are scaffolded next."
          : "File roles, key role, and integrations are scaffolded next."}
      </p>
    </div>
  );
}
