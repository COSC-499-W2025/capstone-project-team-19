# Testing

## Test Strategy

The system was tested using a combination of:

- **Unit Testing**: Individual modules were tested using `pytest`
- **Integration Testing**: End-to-end flows were tested across modules (e.g., upload --> analysis --> storage)
- **Manual Testing (CLI)**: Realistic project ZIP files were uploaded and processed to validate system behavior.

## Running Tests

Run the automated test suite from the root directory:

```bash
pytest tests
```

## Test Data

Test data is located in the `test-data/` directory.

It includes:

- **Versioned project data**: Used to test deduplication and version tracking
- **Multi-project dataset**: Includes individual and collaborative, code and text projects

These datasets are used in manual CLI testing to validate system behavior across different scenarios.

## Manual Testing (CLI)

### Preparing Input Data (ZIP Upload)

This section describes how to structure input data for testing the system using the CLI.

To keep analysis simple, please structure the folder you zip and upload like this:

1. Place everything inside a single top-level directory (your "root" folder). The ZIP should contain only this folder at its highest level.
2. Inside the root folder you may optionally create subfolders named `individual/` and `collaborative/`.
   - If you create these folders, add each project as a subfolder beneath the appropriate one. Every subfolder under `individual/` is treated as an individual project; every subfolder under `collaborative/` is treated as a collaborative project.
3. If you do **not** create `individual/` or `collaborative/`, simply keep each project as a child folder directly under the root. The CLI will then ask you to classify each project one-by-one.
   - Any loose files left directly in the root (not inside a project folder) are ignored during analysis, so be sure to nest everything you want processed inside a project directory.

Example structures:

```
my-workspace/
├── individual/
│   ├── blog-site/
│   └── data-journal/
└── collaborative/
    ├── hackathon-app/
    └── research-tool/
```

or, if you prefer to classify through the prompts:

```
my-workspace/
├── blog-site/
├── data-journal/
├── hackathon-app/
└── research-tool/
```

After arranging your files, zip the root folder (e.g., zip `my-workspace/` into `my-workspace.zip`) and provide that ZIP file path to the CLI when prompted.

> **Note:**
> Do not change the name of the ZIP folder, it should match the root folder exactly.
> Local .git analysis will not work if the folder names do not match.


### Example Test Flows