import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchThumbnailUrl } from "../api/projects";

type Props = {
  projectId: number;
  name: string;
};

function fallbackColor(): string {
  const rgb=[0.7246,0.7246, 0.7246
  ];
  return `hsl(${rgb}, 50%, 68%)`;
}

export default function ProjectCard({ projectId, name }: Props) {
  const nav = useNavigate();
  const [thumbUrl, setThumbUrl] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    fetchThumbnailUrl(projectId).then((url) => {
      objectUrl = url;
      setThumbUrl(url);
    });
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [projectId]);

  return (
    <div className="projectCard" onClick={() => nav(`/projects/${projectId}`)}>
      <div
        className="projectCardThumb"
        style={
          thumbUrl
            ? { backgroundImage: `url(${thumbUrl})` }
            : { background: fallbackColor() }
        }
      />
      <div className="projectCardTitle">{name}</div>
    </div>
  );
}
