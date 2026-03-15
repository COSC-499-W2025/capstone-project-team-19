import { useEffect, useMemo, useState } from "react";
import type { DriveFile, MainFileSection, UploadProjectFilesRecord } from "../../../../../api/uploads";
import type { SetupFlowResult, SetupProjectCard } from "../../types";

type Props = {
  project: SetupProjectCard;
  actions: SetupFlowResult["actions"];
  isMutating: boolean;
};

function toggleString(values: string[], value: string): string[] {
  if (values.includes(value)) return values.filter((item) => item !== value);
  return [...values, value];
}

function toggleNumber(values: number[], value: number): number[] {
  if (values.includes(value)) return values.filter((item) => item !== value);
  return [...values, value].sort((a, b) => a - b);
}

export default function TextSetupSection({ project, actions, isMutating }: Props) {
  const [filesPayload, setFilesPayload] = useState<UploadProjectFilesRecord | null>(null);
  const [filesLoading, setFilesLoading] = useState(false);
  const [mainFile, setMainFile] = useState(project.mainFileRelpath ?? "");
  const [sections, setSections] = useState<MainFileSection[]>([]);
  const [sectionsLoading, setSectionsLoading] = useState(false);
  const [selectedSectionIds, setSelectedSectionIds] = useState<number[]>(project.mainSectionIds);
  const [selectedSupportingText, setSelectedSupportingText] = useState<string[]>(project.supportingTextRelpaths);
  const [selectedSupportingCsv, setSelectedSupportingCsv] = useState<string[]>(project.supportingCsvRelpaths);
  const [driveChoice, setDriveChoice] = useState<"" | "yes" | "no">(
    project.driveState === "connected" ? "yes" : project.driveState === "skipped" ? "no" : "",
  );
  const [driveSearch, setDriveSearch] = useState("");
  const [selectedLocalFile, setSelectedLocalFile] = useState("");
  const [driveFiles, setDriveFiles] = useState<DriveFile[]>([]);
  const [driveLoading, setDriveLoading] = useState(false);
  const [selectedDriveFileId, setSelectedDriveFileId] = useState("");
  const [driveMapByLocalFile, setDriveMapByLocalFile] = useState<Record<string, DriveFile>>({});
  const [driveMessage, setDriveMessage] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    setMainFile(project.mainFileRelpath ?? "");
    setSelectedSectionIds(project.mainSectionIds);
    setSelectedSupportingText(project.supportingTextRelpaths);
    setSelectedSupportingCsv(project.supportingCsvRelpaths);
    setDriveChoice(project.driveState === "connected" ? "yes" : project.driveState === "skipped" ? "no" : "");
  }, [
    project.mainFileRelpath,
    project.mainSectionIds,
    project.supportingCsvRelpaths,
    project.supportingTextRelpaths,
    project.driveState,
  ]);

  useEffect(() => {
    if (project.projectKey === null) return;
    const projectKey = project.projectKey;
    let active = true;

    async function loadFiles() {
      setFilesLoading(true);
      const data = await actions.getProjectFiles(projectKey);
      if (!active) return;
      setFilesPayload(data);
      setFilesLoading(false);
    }

    loadFiles();
    return () => {
      active = false;
    };
  }, [actions, project.projectKey]);

  const mainFileOptions = useMemo(() => {
    if (!filesPayload) return [];
    return filesPayload.text_files.length > 0 ? filesPayload.text_files : filesPayload.all_files;
  }, [filesPayload]);

  const supportingTextOptions = useMemo(() => {
    if (!filesPayload) return [];
    return filesPayload.text_files.filter((item) => item.relpath !== mainFile);
  }, [filesPayload, mainFile]);

  const supportingCsvOptions = useMemo(() => {
    if (!filesPayload) return [];
    return filesPayload.csv_files;
  }, [filesPayload]);
  const driveLocalFiles = useMemo(() => filesPayload?.all_files ?? [], [filesPayload]);
  const filteredDriveResults = useMemo(
    () =>
      driveSearch.trim()
        ? driveFiles.filter((item) => item.name.toLowerCase().includes(driveSearch.trim().toLowerCase()))
        : driveFiles,
    [driveFiles, driveSearch],
  );
  const mappedDriveCount = useMemo(
    () => Object.keys(driveMapByLocalFile).filter((name) => Boolean(driveMapByLocalFile[name])).length,
    [driveMapByLocalFile],
  );
  const showCollaborativeDriveUi = project.projectType === "text" && project.classification === "collaborative";

  useEffect(() => {
    if (driveLocalFiles.length === 0) {
      setSelectedLocalFile("");
      return;
    }
    if (selectedLocalFile) return;
    setSelectedLocalFile(driveLocalFiles[0].file_name);
  }, [driveLocalFiles, selectedLocalFile]);

  useEffect(() => {
    if (project.driveState !== "connected") return;
    let active = true;
    async function loadDriveFiles() {
      setDriveLoading(true);
      const data = await actions.driveFiles(project.projectName);
      if (!active) return;
      setDriveFiles(data?.files ?? []);
      setDriveLoading(false);
    }
    loadDriveFiles();
    return () => {
      active = false;
    };
  }, [actions, project.driveState, project.projectName]);

  async function onSaveMainFile() {
    if (project.projectKey === null || !mainFile) return;
    const data = await actions.setMainFile(project.projectKey, mainFile);
    if (!data) return;
    setSaveMessage("Main file saved.");
  }

  async function onLoadSections() {
    if (project.projectKey === null) return;
    if (!mainFile) {
      setSaveMessage("Select and save a main file first.");
      return;
    }
    setSectionsLoading(true);
    const data = await actions.getMainFileSections(project.projectKey);
    setSectionsLoading(false);
    if (!data) return;
    setSections(data.sections);
  }

  async function onSaveSections() {
    if (project.projectKey === null) return;
    const data = await actions.setContributedSections(project.projectKey, selectedSectionIds);
    if (!data) return;
    setSaveMessage("Contributed sections saved.");
  }

  async function onSaveSupportingText() {
    if (project.projectKey === null) return;
    const data = await actions.setSupportingTextFiles(project.projectKey, selectedSupportingText);
    if (!data) return;
    setSaveMessage("Supporting text files saved.");
  }

  async function onSaveSupportingCsv() {
    if (project.projectKey === null) return;
    const data = await actions.setSupportingCsvFiles(project.projectKey, selectedSupportingCsv);
    if (!data) return;
    setSaveMessage("Supporting CSV files saved.");
  }

  function onSelectDriveResult(id: string) {
    setSelectedDriveFileId(id);
  }

  function onMapSelectedFile() {
    if (!selectedLocalFile || !selectedDriveFileId) return;
    const selectedDrive = driveFiles.find((item) => item.id === selectedDriveFileId);
    if (!selectedDrive) return;
    setDriveMapByLocalFile((prev) => ({ ...prev, [selectedLocalFile]: selectedDrive }));
  }

  function onResetDriveMapping() {
    setSelectedDriveFileId("");
    setDriveMapByLocalFile({});
  }

  async function onApplyDriveChoice() {
    setDriveMessage(null);
    if (driveChoice === "") return;
    if (driveChoice === "no") {
      const data = await actions.driveStart(project.projectName, false);
      if (!data) return;
      setDriveFiles([]);
      setDriveMessage("Google Drive skipped for now.");
      return;
    }

    const data = await actions.driveStart(project.projectName, true);
    if (!data) return;
    if (data.auth_url) {
      window.open(data.auth_url, "_blank", "noopener,noreferrer");
      setDriveMessage("Authorization opened. Complete it, then click Refresh Drive Files.");
      return;
    }
    setDriveMessage("Google Drive is connected.");
    await onRefreshDriveFiles();
  }

  async function onRefreshDriveFiles() {
    setDriveMessage(null);
    setDriveLoading(true);
    const data = await actions.driveFiles(project.projectName);
    setDriveLoading(false);
    if (!data) return;
    setDriveFiles(data.files);
    setDriveMessage(data.files.length > 0 ? "Drive files loaded." : "No supported Drive files found.");
  }

  async function onFinalizeDriveLinks() {
    const links = Object.entries(driveMapByLocalFile).map(([localFileName, driveFile]) => ({
      local_file_name: localFileName,
      drive_file_id: driveFile.id,
      drive_file_name: driveFile.name,
      mime_type: driveFile.mime_type,
    }));
    if (links.length === 0) {
      setDriveMessage("Select at least one mapping before finalizing.");
      return;
    }
    const data = await actions.driveLink(project.projectName, links);
    if (!data) return;
    setDriveMessage(`Saved ${links.length} Drive file link${links.length > 1 ? "s" : ""}.`);
  }

  return (
    <div className="space-y-4">

      <div className="space-y-3">
        <div className="text-sm font-semibold text-zinc-900">Main file</div>
        {filesLoading && <p className="text-sm text-zinc-600">Loading project files...</p>}
        {!filesLoading && mainFileOptions.length === 0 && (
          <p className="text-sm text-zinc-600">No text files found for this project.</p>
        )}
        {!filesLoading && mainFileOptions.length > 0 && (
          <>
            <select
              value={mainFile}
              onChange={(event) => setMainFile(event.target.value)}
              className="h-12 w-full rounded border border-zinc-300 bg-zinc-50 px-4 py-3 text-sm text-zinc-700"
              disabled={isMutating}
            >
              <option value="">Select main file</option>
              {mainFileOptions.map((item) => (
                <option key={item.relpath} value={item.relpath}>
                  {item.file_name}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={onSaveMainFile}
              disabled={isMutating || !mainFile || project.projectKey === null}
              className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
            >
              Save main file
            </button>
          </>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="text-sm font-semibold text-zinc-900">Contributed sections</div>
          <button
            type="button"
            onClick={onLoadSections}
            disabled={isMutating || sectionsLoading || project.projectKey === null}
            className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
          >
            {sectionsLoading ? "Loading..." : "Load sections"}
          </button>
        </div>

        {sections.length === 0 && (
          <p className="text-sm text-zinc-600">No sections loaded yet. Load sections after saving a main file.</p>
        )}

        {sections.length > 0 && (
          <div className="space-y-1">
            {sections.map((section) => (
              <label key={section.id} className="flex items-start gap-2 text-sm text-zinc-800">
                <input
                  type="checkbox"
                  checked={selectedSectionIds.includes(section.id)}
                  onChange={() => setSelectedSectionIds((prev) => toggleNumber(prev, section.id))}
                  disabled={isMutating}
                />
                <span>
                  <span className="font-medium">{section.title}</span>
                  {section.preview ? ` - ${section.preview}` : ""}
                </span>
              </label>
            ))}
            <button
              type="button"
              onClick={onSaveSections}
              disabled={isMutating || project.projectKey === null}
              className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
            >
              Save section selection
            </button>
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div className="text-sm font-semibold text-zinc-900">Supporting text files</div>
        {supportingTextOptions.length === 0 && (
          <p className="text-sm text-zinc-600">No supporting text candidates found.</p>
        )}
        {supportingTextOptions.length > 0 && (
          <div className="space-y-1">
            {supportingTextOptions.map((item) => (
              <label key={item.relpath} className="flex items-center gap-2 text-sm text-zinc-800">
                <input
                  type="checkbox"
                  checked={selectedSupportingText.includes(item.relpath)}
                  onChange={() => setSelectedSupportingText((prev) => toggleString(prev, item.relpath))}
                  disabled={isMutating}
                />
                <span>{item.file_name}</span>
              </label>
            ))}
            <button
              type="button"
              onClick={onSaveSupportingText}
              disabled={isMutating || project.projectKey === null}
              className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
            >
              Save supporting text files
            </button>
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div className="text-sm font-semibold text-zinc-900">Supporting CSV files</div>
        {supportingCsvOptions.length === 0 && (
          <p className="text-sm text-zinc-600">No supporting CSV files found.</p>
        )}
        {supportingCsvOptions.length > 0 && (
          <div className="space-y-1">
            {supportingCsvOptions.map((item) => (
              <label key={item.relpath} className="flex items-center gap-2 text-sm text-zinc-800">
                <input
                  type="checkbox"
                  checked={selectedSupportingCsv.includes(item.relpath)}
                  onChange={() => setSelectedSupportingCsv((prev) => toggleString(prev, item.relpath))}
                  disabled={isMutating}
                />
                <span>{item.file_name}</span>
              </label>
            ))}
            <button
              type="button"
              onClick={onSaveSupportingCsv}
              disabled={isMutating || project.projectKey === null}
              className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
            >
              Save supporting CSV files
            </button>
          </div>
        )}
      </div>

      {showCollaborativeDriveUi && (
        <div className="space-y-3 rounded-lg border border-zinc-300 bg-zinc-50 p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-zinc-900">
              Connect Google Drive for collaborative text mapping?
            </p>
            <div className="flex items-center gap-5 text-sm text-zinc-800">
              <label className="flex items-center gap-1.5">
                <input
                  type="radio"
                  name={`drive-choice-${project.projectName}`}
                  value="yes"
                  checked={driveChoice === "yes"}
                  onChange={() => setDriveChoice("yes")}
                  disabled={isMutating}
                />
                <span>Yes</span>
              </label>
              <label className="flex items-center gap-1.5">
                <input
                  type="radio"
                  name={`drive-choice-${project.projectName}`}
                  value="no"
                  checked={driveChoice === "no"}
                  onChange={() => setDriveChoice("no")}
                  disabled={isMutating}
                />
                <span>No</span>
              </label>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onApplyDriveChoice}
              disabled={isMutating || driveChoice === ""}
              className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
            >
              {driveChoice === "no" ? "Skip Drive" : "Connect Drive"}
            </button>
            <button
              type="button"
              onClick={onRefreshDriveFiles}
              disabled={isMutating || driveChoice !== "yes"}
              className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
            >
              Refresh Drive Files
            </button>
          </div>
          <p className="text-sm text-zinc-700">
            Current state: <span className="font-medium">{project.driveState}</span>
            {project.driveLinkedFilesCount > 0 ? ` | Linked files: ${project.driveLinkedFilesCount}` : ""}
          </p>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-zinc-300 bg-white p-3">
              <div className="mb-2 text-sm font-semibold text-zinc-900">Files ({project.projectName})</div>
              <div className="space-y-2">
                {driveLocalFiles.length === 0 && <p className="text-sm text-zinc-600">No project files found.</p>}
                {driveLocalFiles.map((item, index) => {
                  const selected = selectedLocalFile === item.file_name;
                  const mappedName = driveMapByLocalFile[item.file_name];
                  return (
                    <button
                      key={`${item.relpath}-${index}`}
                      type="button"
                      onClick={() => setSelectedLocalFile(item.file_name)}
                      className={`w-full rounded border px-3 py-2 text-left text-sm ${selected ? "border-zinc-500 bg-zinc-100" : "border-zinc-200 bg-zinc-50"}`}
                    >
                      <div className="font-medium text-zinc-900">{index + 1}. {item.file_name}</div>
                      <div className="mt-1 text-xs text-zinc-600">
                        Mapping: {mappedName ? mappedName.name : "Not selected"}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="rounded-lg border border-zinc-300 bg-white p-3">
              <div className="mb-2 text-sm font-semibold text-zinc-900">
                Find Drive For: {selectedLocalFile || "Select a file"}
              </div>
              <div className="mb-3 flex gap-2">
                <input
                  value={driveSearch}
                  onChange={(event) => setDriveSearch(event.target.value)}
                  placeholder="Search Drive files by name..."
                  className="h-10 flex-1 rounded border border-zinc-300 px-3 text-sm text-zinc-700"
                  disabled={isMutating || driveChoice !== "yes"}
                />
                <button
                  type="button"
                  className="rounded border border-zinc-300 bg-white px-3 text-sm font-medium text-zinc-900"
                  onClick={onRefreshDriveFiles}
                  disabled={isMutating || driveChoice !== "yes" || driveLoading}
                >
                  {driveLoading ? "Loading..." : "Search"}
                </button>
              </div>

              <div className="space-y-2">
                {driveLoading && <p className="text-sm text-zinc-600">Loading Drive files...</p>}
                {filteredDriveResults.length === 0 && (
                  <p className="text-sm text-zinc-600">
                    {driveChoice === "yes" ? "No matching Drive files." : "Select Yes to start mapping."}
                  </p>
                )}
                {filteredDriveResults.map((item) => {
                  const selected = selectedDriveFileId === item.id;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => onSelectDriveResult(item.id)}
                      disabled={driveChoice !== "yes"}
                      className={`w-full rounded border px-3 py-2 text-left text-sm disabled:opacity-60 ${selected ? "border-emerald-400 bg-emerald-50" : "border-zinc-200 bg-zinc-50"}`}
                    >
                      <div className="font-medium text-zinc-900">{item.name}</div>
                      <div className="text-xs text-zinc-600">{item.mime_type}</div>
                    </button>
                  );
                })}
              </div>

              <div className="mt-3 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={onMapSelectedFile}
                  disabled={driveChoice !== "yes" || !selectedLocalFile || !selectedDriveFileId}
                  className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
                >
                  Select
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between rounded border border-zinc-300 bg-white px-3 py-2 text-sm">
            <span className="text-zinc-700">Mapped: {mappedDriveCount} of {driveLocalFiles.length} files</span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onResetDriveMapping}
                className="rounded border border-zinc-300 bg-white px-3 py-1.5 font-medium text-zinc-900"
              >
                Reset
              </button>
              <button
                type="button"
                onClick={onFinalizeDriveLinks}
                disabled={isMutating || mappedDriveCount <= 0}
                className="rounded border border-zinc-300 bg-zinc-900 px-3 py-1.5 font-medium text-white disabled:opacity-50"
              >
                Finalize
              </button>
            </div>
          </div>
          {driveMessage && <p className="text-sm text-zinc-700">{driveMessage}</p>}
        </div>
      )}

      {saveMessage && <p className="text-sm text-zinc-700">{saveMessage}</p>}
    </div>
  );
}
