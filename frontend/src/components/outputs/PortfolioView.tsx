type Props = {
  onBack: () => void;
};

export default function PortfolioView({ onBack }: Props) {
  return (
    <div className="content">
      <div className="outputsHeader">
        <button className="backBtn" onClick={onBack}>&larr;</button>
        <h2>Portfolio</h2>
      </div>
      <hr className="divider" />
      <div className="cardWide">
        <p>Coming soon.</p>
      </div>
    </div>
  );
}
