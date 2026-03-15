import { useEffect, useMemo, useState } from "react";
import type { MainFileSection, UploadProjectFilesRecord } from "../../../../../api/uploads";
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

  async function onSaveDriveChoice() {
    setDriveMessage(null);
    if (driveChoice === "no") {
      const data = await actions.driveStart(project.projectName, false);
      if (!data) return;
      setDriveMessage("Google Drive skipped for now.");
      return;
    }
    if (driveChoice === "yes") {
      setDriveMessage("Google Drive connection UI is coming soon.");
    }
  }

  return (
    <div className="space-y-3 rounded-lg border border-zinc-200 bg-white px-3 py-2">
      <h4 className="text-sm leading-tight font-semibold text-zinc-900">Text Setup</h4>

      <div className="space-y-2 rounded border border-zinc-200 bg-zinc-50 px-2 py-2">
        <div className="text-xs font-semibold text-zinc-900">Main file</div>
        {filesLoading && <p className="text-xs text-zinc-600">Loading project files...</p>}
        {!filesLoading && mainFileOptions.length === 0 && (
          <p className="text-xs text-zinc-600">No text files found for this project.</p>
        )}
        {!filesLoading && mainFileOptions.length > 0 && (
          <>
            <select
              value={mainFile}
              onChange={(event) => setMainFile(event.target.value)}
              className="h-8 w-full rounded border border-zinc-300 bg-white px-2 text-xs"
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
              className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
            >
              Save main file
            </button>
          </>
        )}
      </div>

      <div className="space-y-2 rounded border border-zinc-200 bg-zinc-50 px-2 py-2">
        <div className="flex items-center justify-between gap-2">
          <div className="text-xs font-semibold text-zinc-900">Contributed sections</div>
          <button
            type="button"
            onClick={onLoadSections}
            disabled={isMutating || sectionsLoading || project.projectKey === null}
            className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
          >
            {sectionsLoading ? "Loading..." : "Load sections"}
          </button>
        </div>

        {sections.length === 0 && (
          <p className="text-xs text-zinc-600">No sections loaded yet. Load sections after saving a main file.</p>
        )}

        {sections.length > 0 && (
          <div className="space-y-1">
            {sections.map((section) => (
              <label key={section.id} className="flex items-start gap-2 text-xs text-zinc-800">
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
              className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
            >
              Save section selection
            </button>
          </div>
        )}
      </div>

      <div className="space-y-2 rounded border border-zinc-200 bg-zinc-50 px-2 py-2">
        <div className="text-xs font-semibold text-zinc-900">Supporting text files</div>
        {supportingTextOptions.length === 0 && (
          <p className="text-xs text-zinc-600">No supporting text candidates found.</p>
        )}
        {supportingTextOptions.length > 0 && (
          <div className="space-y-1">
            {supportingTextOptions.map((item) => (
              <label key={item.relpath} className="flex items-center gap-2 text-xs text-zinc-800">
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
              className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
            >
              Save supporting text files
            </button>
          </div>
        )}
      </div>

      <div className="space-y-2 rounded border border-zinc-200 bg-zinc-50 px-2 py-2">
        <div className="text-xs font-semibold text-zinc-900">Supporting CSV files</div>
        {supportingCsvOptions.length === 0 && (
          <p className="text-xs text-zinc-600">No supporting CSV files found.</p>
        )}
        {supportingCsvOptions.length > 0 && (
          <div className="space-y-1">
            {supportingCsvOptions.map((item) => (
              <label key={item.relpath} className="flex items-center gap-2 text-xs text-zinc-800">
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
              className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
            >
              Save supporting CSV files
            </button>
          </div>
        )}
      </div>

      <div className="space-y-2 rounded border border-zinc-200 bg-zinc-50 px-2 py-2">
        <div className="text-xs font-semibold text-zinc-900">Google Drive (placeholder)</div>
        <p className="text-xs text-zinc-700">
          Current state: <span className="font-medium">{project.driveState}</span>
          {project.driveLinkedFilesCount > 0 ? ` | Linked files: ${project.driveLinkedFilesCount}` : ""}
        </p>
        <div className="flex items-center gap-4 text-xs text-zinc-800">
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
        <button
          type="button"
          onClick={onSaveDriveChoice}
          disabled={isMutating || driveChoice === ""}
          className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
        >
          Save Drive preference
        </button>
        {driveMessage && <p className="text-xs text-zinc-700">{driveMessage}</p>}
      </div>

      {saveMessage && <p className="text-xs text-zinc-700">{saveMessage}</p>}
    </div>
  );
}
