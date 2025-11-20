# Database Module Documentation

## Overview
The `src/db` directory contains all SQL-related logic for the system. All database reads and writes must go through this directory. No inline SQL should appear anywhere else in the codebase.

Each file represents a domain or table group in the database schema. This structure makes database operations easier to maintain, test, and refactor.

---

## How to Add a New Database Function

### 1. Choose the correct module
Select the file based on the table or domain you're working with.  
Before adding a new helper, verify that a similar query or operation does not already exist in the appropriate module.

### 2. Add the function to `__init__.py` in `src/db/`
After creating a DB helper, expose it through the package API.

Example import inside `__init__.py`:

```python
from .files import get_files_for_project
```

Then add its name to `__all__`:
```python
"get_files_for_project",
```

This allows clean imports elsewhere in the codebase:
```python
from src.db import get_files_for_project
```

## Notes
- All SQL operations belong inside the `src/db` directory
- Avoid duplicating existing helpers
- Keep helpers focused: each should perform one clear, well-defined database action