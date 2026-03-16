import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchThumbnailUrl } from "../api/projects";

type Props = {
  projectId: number;
  name: string;
  /** Base path for the project detail link. Defaults to "/projects". */
  basePath?: string;
  /** Custom thumbnail fetcher. Defaults to the private fetchThumbnailUrl. */
  thumbnailFetcher?: (projectId: number) => Promise<string | null>;
};

function fallbackColor(): string {
  const rgb=[0.7246,0.7246, 0.7246
  ];
  return `rgb(${rgb.map((c) => Math.round(c * 255)).join(",")})`;
}

export default function ProjectCard({
  projectId,
  name,
  basePath = "/projects",
  thumbnailFetcher = fetchThumbnailUrl,
}: Props) {
  const nav = useNavigate();
  const [thumbUrl, setThumbUrl] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    thumbnailFetcher(projectId).then((url) => {
      objectUrl = url;
      setThumbUrl(url);
    });
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [projectId, thumbnailFetcher]);

  return (
    <div className="projectCard" onClick={() => nav(`${basePath}/${projectId}`)}>
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
