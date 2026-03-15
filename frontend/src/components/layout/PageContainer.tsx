type Props = {
  children: React.ReactNode;
  className?: string;
};

export default function PageContainer({ children, className = "" }: Props) {
  return <main className={`pageContainer ${className}`}>{children}</main>;
}