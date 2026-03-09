import type { ChangeEvent, DragEvent, RefObject } from "react";

type Props = {
  selectedFile: File | null;
  sizeLabel: string | null;
  dragActive: boolean;
  uploadInputRef: RefObject<HTMLInputElement | null>;
  onFileInputChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onDragOver: (event: DragEvent<HTMLDivElement>) => void;
  onDragLeave: () => void;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
  onSelectFileClick: () => void;
};

export default function UploadStage({
  selectedFile,
  sizeLabel,
  dragActive,
  uploadInputRef,
  onFileInputChange,
  onDragOver,
  onDragLeave,
  onDrop,
  onSelectFileClick,
}: Props) {
  return (
    <div className="uploadStagePanel">
      <h2 className="wizardPlaceholderTitle">Upload</h2>

      <div className="uploadIntroRow">
        <div className="uploadIntroText">
          <p>Only ZIP files are accepted.</p>
          <p>
            We treat each folder inside a zip file as one project. Optionally, you can organize projects under{" "}
            <code>individual/</code> and <code>collaborative/</code>, then place project folders inside those.
          </p>
          <p>
            If you use <code>individual/</code> and <code>collaborative/</code>, classification can be auto-detected. If
            not, we&apos;ll ask classification during upload.
          </p>
          <p>
            After upload, projects are compared with other projects in the same or previous uploads to detect duplicates or
            existing history.
          </p>
        </div>

        <div className="uploadStructureCard" aria-label="Upload structure example">
          <div className="uploadStructureTitle">Example ZIP structure</div>
          <pre className="uploadStructurePre">
{`projects.zip
    individual/
        ProjectA/
        ProjectB/
    collaborative/
        ProjectC/`}
          </pre>
        </div>
      </div>

      <input
        ref={uploadInputRef}
        type="file"
        accept=".zip,application/zip,application/x-zip-compressed"
        className="uploadFileInput"
        onChange={onFileInputChange}
      />

      <div
        className={`uploadDropZone${dragActive ? " uploadDropZone--active" : ""}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <div className="uploadDropLeft">
          <div className="uploadDropTitle">Select a file or drag and drop here</div>
          <div className="uploadDropHint">ZIP file only</div>
        </div>

        <button type="button" className="uploadSelectBtn" onClick={onSelectFileClick}>
          SELECT FILE
        </button>
      </div>

      <div className="uploadFileAddedBlock">
        <h3 className="uploadFileAddedTitle">File added</h3>
        <p className="uploadFileAddedHint">
          If you want to change your file selection, choose a new ZIP using the SELECT FILE button above.
        </p>
        {selectedFile ? (
          <div className="uploadFileRow">
            <span className="uploadFileName">{selectedFile.name}</span>
            <span className="uploadFileSize">{sizeLabel}</span>
          </div>
        ) : (
          <div className="uploadFileEmpty">No file selected yet.</div>
        )}
      </div>
    </div>
  );
}
