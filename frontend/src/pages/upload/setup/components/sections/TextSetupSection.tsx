import { useEffect, useMemo, useRef, useState } from "react";
import type { DriveFile, MainFileSection, UploadProjectFilesRecord } from "../../../../../api/uploads";
import type { SetupFlowResult, SetupProjectCard } from "../../types";
import { setupPrimaryActionButtonClass, setupSecondaryActionButtonClass } from "./buttonStyles";

type Props = {
  project: SetupProjectCard;
  actions: SetupFlowResult["actions"];
  refreshUpload: SetupFlowResult["refreshUpload"];
  isMutating: boolean;
};

const DRIVE_PAGE_SIZE = 5;
const DRIVE_OAUTH_MESSAGE_SOURCE = "capstone-google-drive-oauth";
const DRIVE_OAUTH_POLL_INTERVAL_MS = 1500;
const DRIVE_OAUTH_MAX_POLL_ATTEMPTS = 40;

function toggleString(values: string[], value: string): string[] {
  if (values.includes(value)) return values.filter((item) => item !== value);
  return [...values, value];
}

function toggleNumber(values: number[], value: number): number[] {
  if (values.includes(value)) return values.filter((item) => item !== value);
  return [...values, value].sort((a, b) => a - b);
}

function isCsvRelpath(relpath: string): boolean {
  return relpath.trim().toLowerCase().endsWith(".csv");
}

type DriveOauthMessage = {
  source?: string;
  status?: string;
  project_name?: string;
};

function asDriveOauthMessage(value: unknown): DriveOauthMessage | null {
  if (!value || typeof value !== "object") return null;
  return value as DriveOauthMessage;
}

export default function TextSetupSection({ project, actions, refreshUpload, isMutating }: Props) {
  const [filesPayload, setFilesPayload] = useState<UploadProjectFilesRecord | null>(null);
  const [filesLoading, setFilesLoading] = useState(false);
  const [mainFile, setMainFile] = useState(project.mainFileRelpath ?? "");
  const [sections, setSections] = useState<MainFileSection[]>([]);
  const [sectionsLoading, setSectionsLoading] = useState(false);
  const [selectedSectionIds, setSelectedSectionIds] = useState<number[]>(project.mainSectionIds);
  const [selectedSupportingText, setSelectedSupportingText] = useState<string[]>(project.supportingTextRelpaths);
  const [selectedSupportingCsv, setSelectedSupportingCsv] = useState<string[]>(project.supportingCsvRelpaths);
  const [driveSearch, setDriveSearch] = useState("");
  const [selectedLocalFile, setSelectedLocalFile] = useState("");
  const [driveFiles, setDriveFiles] = useState<DriveFile[]>([]);
  const [driveFilesLoaded, setDriveFilesLoaded] = useState(false);
  const [driveLoading, setDriveLoading] = useState(false);
  const [selectedDriveFileId, setSelectedDriveFileId] = useState("");
  const [driveMapByLocalFile, setDriveMapByLocalFile] = useState<Record<string, DriveFile>>({});
  const [driveMessage, setDriveMessage] = useState<string | null>(null);
  const [awaitingDriveOauthReturn, setAwaitingDriveOauthReturn] = useState(false);
  const [drivePagerButtonsWidth, setDrivePagerButtonsWidth] = useState<number | null>(null);
  const drivePagerButtonsRef = useRef<HTMLDivElement | null>(null);
  const [localPage, setLocalPage] = useState(1);
  const [drivePage, setDrivePage] = useState(1);
  const [mainFileSaveMessage, setMainFileSaveMessage] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    setMainFile(project.mainFileRelpath ?? "");
    setSelectedSectionIds(project.mainSectionIds);
    setSelectedSupportingText(project.supportingTextRelpaths.filter((relpath) => !isCsvRelpath(relpath)));
    setSelectedSupportingCsv(project.supportingCsvRelpaths);
  }, [
    project.mainFileRelpath,
    project.mainSectionIds,
    project.supportingCsvRelpaths,
    project.supportingTextRelpaths,
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
    return filesPayload.text_files.filter((item) => item.relpath !== mainFile && !isCsvRelpath(item.relpath));
  }, [filesPayload, mainFile]);

  const supportingCsvOptions = useMemo(() => {
    if (!filesPayload) return [];
    return filesPayload.csv_files;
  }, [filesPayload]);
  const mainFileStatusMessage = mainFileSaveMessage ?? (project.mainFileRelpath ? "Main file saved." : null);
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
  const isDriveConnected = project.driveState === "connected";
  const showSupportingFilePicker =
    project.projectType === "text" && project.classification === "collaborative";
  const showContributionSectionPicker =
    project.projectType === "text" && project.classification === "collaborative";
  const showCollaborativeDriveUi = project.projectType === "text" && project.classification === "collaborative";
  const localPageCount = useMemo(
    () => Math.max(1, Math.ceil(driveLocalFiles.length / DRIVE_PAGE_SIZE)),
    [driveLocalFiles.length],
  );
  const safeLocalPage = Math.min(localPage, localPageCount);
  const localPageStart = (safeLocalPage - 1) * DRIVE_PAGE_SIZE;
  const localPageFiles = useMemo(
    () => driveLocalFiles.slice(localPageStart, localPageStart + DRIVE_PAGE_SIZE),
    [driveLocalFiles, localPageStart],
  );
  const drivePageCount = useMemo(
    () => Math.max(1, Math.ceil(filteredDriveResults.length / DRIVE_PAGE_SIZE)),
    [filteredDriveResults.length],
  );
  const safeDrivePage = Math.min(drivePage, drivePageCount);
  const drivePageStart = (safeDrivePage - 1) * DRIVE_PAGE_SIZE;
  const drivePageFiles = useMemo(
    () => filteredDriveResults.slice(drivePageStart, drivePageStart + DRIVE_PAGE_SIZE),
    [filteredDriveResults, drivePageStart],
  );

  useEffect(() => {
    if (driveLocalFiles.length === 0) {
      setSelectedLocalFile("");
      return;
    }
    if (selectedLocalFile) return;
    setSelectedLocalFile(driveLocalFiles[0].file_name);
  }, [driveLocalFiles, selectedLocalFile]);

  useEffect(() => {
    if (!isDriveConnected) return;
    setAwaitingDriveOauthReturn(false);
    setDriveMessage((prev) => (prev === "Google Drive authorization opened in a new tab." ? "Google Drive is connected." : prev));
  }, [isDriveConnected]);

  useEffect(() => {
    if (awaitingDriveOauthReturn) return;
    if (isDriveConnected) return;
    setDriveFiles([]);
    setDriveFilesLoaded(false);
    setDriveMapByLocalFile({});
    setSelectedDriveFileId("");
    setDriveSearch("");
    setDrivePage(1);
  }, [awaitingDriveOauthReturn, isDriveConnected]);

  useEffect(() => {
    if (!awaitingDriveOauthReturn || isDriveConnected) return;
    let active = true;
    let refreshing = false;
    let pollAttempts = 0;

    async function refreshOnReturn() {
      if (!active || refreshing) return;
      refreshing = true;
      await refreshUpload();
      refreshing = false;
    }

    function onFocus() {
      void refreshOnReturn();
    }

    function onVisibilityChange() {
      if (document.visibilityState === "visible") {
        void refreshOnReturn();
      }
    }

    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibilityChange);

    const pollId = window.setInterval(() => {
      if (!active || isDriveConnected) return;
      pollAttempts += 1;
      if (pollAttempts > DRIVE_OAUTH_MAX_POLL_ATTEMPTS) {
        setAwaitingDriveOauthReturn(false);
        return;
      }
      if (document.visibilityState === "visible") {
        void refreshOnReturn();
      }
    }, DRIVE_OAUTH_POLL_INTERVAL_MS);

    if (document.visibilityState === "visible") {
      void refreshOnReturn();
    }

    return () => {
      active = false;
      window.clearInterval(pollId);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [awaitingDriveOauthReturn, isDriveConnected, refreshUpload]);

  useEffect(() => {
    const node = drivePagerButtonsRef.current;
    if (!node) {
      setDrivePagerButtonsWidth(null);
      return;
    }

    const updateWidth = () => {
      setDrivePagerButtonsWidth(Math.ceil(node.getBoundingClientRect().width));
    };

    updateWidth();

    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(updateWidth);
      observer.observe(node);
      return () => observer.disconnect();
    }

    window.addEventListener("resize", updateWidth);
    return () => {
      window.removeEventListener("resize", updateWidth);
    };
  }, [filteredDriveResults.length]);

  useEffect(() => {
    function onDriveOauthMessage(event: MessageEvent) {
      const data = asDriveOauthMessage(event.data);
      if (!data || data.source !== DRIVE_OAUTH_MESSAGE_SOURCE) return;
      if (data.project_name && data.project_name !== project.projectName) return;

      if (data.status === "connected") {
        setDriveMessage("Google Drive is connected.");
        setAwaitingDriveOauthReturn(false);
        void refreshUpload();
        return;
      }
      if (data.status === "error") {
        setAwaitingDriveOauthReturn(false);
        setDriveMessage("Google Drive authorization failed. Please try connecting again.");
      }
    }

    window.addEventListener("message", onDriveOauthMessage);
    return () => {
      window.removeEventListener("message", onDriveOauthMessage);
    };
  }, [project.projectName, refreshUpload]);

  async function onSaveMainFile() {
    if (project.projectKey === null || !mainFile) return;
    const data = await actions.setMainFile(project.projectKey, mainFile);
    if (!data) return;
    setMainFileSaveMessage("Main file saved.");
    setSaveMessage(null);
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
    const nonCsvRelpaths = selectedSupportingText.filter((relpath) => !isCsvRelpath(relpath));
    const data = await actions.setSupportingTextFiles(project.projectKey, nonCsvRelpaths);
    if (!data) return;
    setSelectedSupportingText(nonCsvRelpaths);
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

  async function onConnectDrive() {
    setAwaitingDriveOauthReturn(false);
    setDriveMessage(null);
    const data = await actions.driveStart(project.projectName, true);
    if (!data) return;
    if (data.auth_url) {
      const authTab = window.open(data.auth_url, "_blank");
      if (!authTab) {
        setDriveMessage("Pop-up blocked. Please allow pop-ups, then click Connect Google Drive again.");
        return;
      }
      setAwaitingDriveOauthReturn(true);
      setDriveMessage("Google Drive authorization opened in a new tab.");
      return;
    }
    setDriveMessage("Google Drive is connected.");
  }

  async function onLoadDriveFiles() {
    setDriveMessage(null);
    setDriveLoading(true);
    const data = await actions.driveFiles(project.projectName);
    setDriveLoading(false);
    if (!data) return;
    setDriveFilesLoaded(true);
    setDriveFiles(data.files);
    setDrivePage(1);
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
        <h4 className="text-lg leading-tight font-semibold text-zinc-900">Main file</h4>
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
              className={setupPrimaryActionButtonClass}
            >
              Save main file
            </button>
            {mainFileStatusMessage && <p className="text-sm text-zinc-700">{mainFileStatusMessage}</p>}
          </>
        )}
      </div>

      {showContributionSectionPicker ? (
        <div className="space-y-3">
          <div className="text-sm font-semibold text-zinc-900">Contributed sections</div>

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
            </div>
          )}

          {sections.length > 0 && selectedSectionIds.length === 0 && (
            <p className="text-sm font-medium text-rose-700">Missing contributed section selection.</p>
          )}

          <button
            type="button"
            onClick={sections.length > 0 ? onSaveSections : onLoadSections}
            disabled={isMutating || sectionsLoading || project.projectKey === null || (!mainFile && sections.length === 0)}
            className={setupPrimaryActionButtonClass}
          >
            {sectionsLoading ? "Loading..." : sections.length > 0 ? "Save section selection" : "Load sections"}
          </button>
        </div>
      ) : (
        <p className="text-sm text-zinc-600">
          Section selection is not needed for individual text projects. All main-file sections are treated as your work.
        </p>
      )}

      {showSupportingFilePicker && (
        <>
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
                  className={setupPrimaryActionButtonClass}
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
                  className={setupPrimaryActionButtonClass}
                >
                  Save supporting CSV files
                </button>
              </div>
            )}
          </div>
        </>
      )}

      {showCollaborativeDriveUi && (
        <div className="space-y-3">
          <h4 className="text-lg leading-tight font-semibold text-zinc-900">Google Drive Integration</h4>
          {!isDriveConnected && (
            <p className="text-sm text-zinc-700">
              <span className="font-semibold">Step 1:</span> Connect your Google Drive account to fetch your files.
            </p>
          )}
          {isDriveConnected && !driveFilesLoaded && (
            <p className="text-sm text-zinc-700">
              <span className="font-semibold">Step 2:</span> Load your Google Drive files.
            </p>
          )}
          {isDriveConnected && driveFilesLoaded && (
            <p className="text-sm text-zinc-700">
              <span className="font-semibold">Step 3:</span> Select matching files and finalize the mapping.
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            {!isDriveConnected && (
              <button
                type="button"
                onClick={onConnectDrive}
                disabled={isMutating}
                className={setupPrimaryActionButtonClass}
              >
                Connect Google Drive
              </button>
            )}
            {isDriveConnected && (
              <button
                type="button"
                onClick={onLoadDriveFiles}
                disabled={isMutating || driveLoading}
                className={driveFilesLoaded ? setupSecondaryActionButtonClass : setupPrimaryActionButtonClass}
              >
                {driveLoading ? "Loading..." : driveFilesLoaded ? "Reload Drive Files" : "Load Drive Files"}
              </button>
            )}
          </div>
          {project.driveLinkedFilesCount > 0 && (
            <p className="text-sm text-zinc-700">
              Linked files: <span className="font-medium">{project.driveLinkedFilesCount}</span>
            </p>
          )}

          {isDriveConnected && driveFilesLoaded && (
            <div className="space-y-3">
              <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-zinc-300 bg-white p-3">
              <div className="mb-2 text-sm font-semibold text-zinc-900">Files ({project.projectName})</div>
              <div className="space-y-2">
                {driveLocalFiles.length === 0 && <p className="text-sm text-zinc-600">No project files found.</p>}
                {localPageFiles.map((item, index) => {
                  const selected = selectedLocalFile === item.file_name;
                  const mappedName = driveMapByLocalFile[item.file_name];
                  return (
                    <button
                      key={item.relpath}
                      type="button"
                      onClick={() => setSelectedLocalFile(item.file_name)}
                      className={`w-full rounded border px-3 py-2 text-left text-sm ${selected ? "border-zinc-500 bg-zinc-100" : "border-zinc-200 bg-zinc-50"}`}
                    >
                      <div className="font-medium text-zinc-900">{localPageStart + index + 1}. {item.file_name}</div>
                      <div className="mt-1 text-xs text-zinc-600">
                        Mapping: {mappedName ? mappedName.name : "Not selected"}
                      </div>
                    </button>
                  );
                })}
                {driveLocalFiles.length > DRIVE_PAGE_SIZE && (
                  <div className="flex items-center justify-between pt-1 text-xs text-zinc-600">
                    <span>Page {safeLocalPage} of {localPageCount}</span>
                    <div ref={drivePagerButtonsRef} className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setLocalPage((page) => Math.max(1, page - 1))}
                        disabled={safeLocalPage <= 1}
                        className="rounded border border-zinc-300 px-2 py-1 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <button
                        type="button"
                        onClick={() => setLocalPage((page) => Math.min(localPageCount, page + 1))}
                        disabled={safeLocalPage >= localPageCount}
                        className="rounded border border-zinc-300 px-2 py-1 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
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
                  className="flex-1 rounded !border !border-zinc-300 !bg-zinc-50 !px-4 !py-3 text-sm text-zinc-700 placeholder:text-zinc-400 disabled:!border-zinc-300 disabled:!bg-zinc-50 disabled:!text-zinc-700 disabled:opacity-100"
                  disabled={isMutating || !isDriveConnected}
                />
                <button
                  type="button"
                  className={setupSecondaryActionButtonClass}
                  onClick={() => setDrivePage(1)}
                  disabled={isMutating || !isDriveConnected || driveLoading}
                >
                  Search
                </button>
              </div>

              <div className="space-y-2">
                {driveLoading && <p className="text-sm text-zinc-600">Loading Drive files...</p>}
                {filteredDriveResults.length === 0 && (
                  <p className="text-sm text-zinc-600">
                    No matching Drive files.
                  </p>
                )}
                {drivePageFiles.map((item) => {
                  const selected = selectedDriveFileId === item.id;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => onSelectDriveResult(item.id)}
                      disabled={!isDriveConnected}
                      className={`w-full rounded border px-3 py-2 text-left text-sm disabled:opacity-60 ${selected ? "border-emerald-400 bg-emerald-50" : "border-zinc-200 bg-zinc-50"}`}
                    >
                      <div className="font-medium text-zinc-900">{item.name}</div>
                      <div className="text-xs text-zinc-600">{item.mime_type}</div>
                    </button>
                  );
                })}
                {filteredDriveResults.length > DRIVE_PAGE_SIZE && (
                  <div className="flex items-center justify-between pt-1 text-xs text-zinc-600">
                    <span>Page {safeDrivePage} of {drivePageCount}</span>
                    <div ref={drivePagerButtonsRef} className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setDrivePage((page) => Math.max(1, page - 1))}
                        disabled={safeDrivePage <= 1}
                        className="rounded border border-zinc-300 px-2 py-1 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <button
                        type="button"
                        onClick={() => setDrivePage((page) => Math.min(drivePageCount, page + 1))}
                        disabled={safeDrivePage >= drivePageCount}
                        className="rounded border border-zinc-300 px-2 py-1 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-3 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={onMapSelectedFile}
                  disabled={!isDriveConnected || !selectedLocalFile || !selectedDriveFileId}
                  className={setupSecondaryActionButtonClass}
                  style={drivePagerButtonsWidth ? { width: `${drivePagerButtonsWidth}px` } : undefined}
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
                    className={setupSecondaryActionButtonClass}
                  >
                    Reset
                  </button>
                  <button
                    type="button"
                    onClick={onFinalizeDriveLinks}
                    disabled={isMutating || mappedDriveCount <= 0}
                    className={setupPrimaryActionButtonClass}
                  >
                    Finalize
                  </button>
                </div>
              </div>
            </div>
          )}
          {driveMessage && <p className="text-sm text-zinc-700">{driveMessage}</p>}
        </div>
      )}

      {saveMessage && <p className="text-sm text-zinc-700">{saveMessage}</p>}
    </div>
  );
}
