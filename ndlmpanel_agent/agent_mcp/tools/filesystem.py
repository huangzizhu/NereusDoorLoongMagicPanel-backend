"""Filesystem, search, and patch tools for coding agents."""

from __future__ import annotations

import os
import fnmatch
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def listFiles(
    path: str = ".",
    recursive: bool = False,
    maxDepth: int = 2,
    limit: int = 200,
    includeHidden: bool = False,
    sortBy: str = "path",
    sortOrder: str = "asc",
) -> dict[str, Any]:
    """List files and directories with path, type, size, and mtime metadata."""
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(str(root))

    max_depth = max(0, int(maxDepth))
    max_items = max(1, int(limit))
    sort_by = _normalizeSortBy(sortBy)
    descending = _normalizeSortOrder(sortOrder) == "desc"

    if root.is_file():
        entries = [_entry(root, root.parent)]
        return {
            "success": True,
            "path": str(root),
            "entries": entries,
            "truncated": False,
            "sortBy": sort_by,
            "sortOrder": "desc" if descending else "asc",
        }

    entries = [_entry(item, root) for item in _iterFiles(root, recursive, max_depth, includeHidden)]
    entries.sort(key=lambda item: _sortKey(item, sort_by), reverse=descending)
    truncated = len(entries) > max_items
    if truncated:
        entries = entries[:max_items]

    return {
        "success": True,
        "path": str(root),
        "entries": entries,
        "truncated": truncated,
        "sortBy": sort_by,
        "sortOrder": "desc" if descending else "asc",
    }


def readFile(
    path: str,
    offset: int = 0,
    limitBytes: int = 65536,
    lineStart: int | None = None,
    lineLimit: int | None = None,
) -> dict[str, Any]:
    """Read text content by byte range or by one-based line range."""
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(str(target))

    _ensureTextFile(target)
    if lineStart is not None:
        return _readFileLines(target, lineStart, lineLimit)
    return _readFileBytes(target, offset, limitBytes)


def _readFileBytes(target: Path, offset: int, limitBytes: int) -> dict[str, Any]:
    start = max(0, int(offset))
    limit = max(1, int(limitBytes))
    size = target.stat().st_size

    with target.open("rb") as file:
        file.seek(start)
        data = file.read(limit + 1)

    truncated = len(data) > limit or start + len(data) < size
    if len(data) > limit:
        data = data[:limit]
    return {
        "success": True,
        "path": str(target),
        "mode": "bytes",
        "offset": start,
        "sizeBytes": size,
        "content": data.decode("utf-8", errors="replace"),
        "truncated": truncated,
    }


def _readFileLines(target: Path, lineStart: int, lineLimit: int | None) -> dict[str, Any]:
    start = max(1, int(lineStart))
    limit = max(1, int(lineLimit)) if lineLimit is not None else 200
    lines = target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    total = len(lines)
    start_index = min(start - 1, total)
    end_index = min(start_index + limit, total)
    selected = lines[start_index:end_index]
    return {
        "success": True,
        "path": str(target),
        "mode": "lines",
        "lineStart": start,
        "lineEnd": start_index + len(selected),
        "lineLimit": limit,
        "totalLines": total,
        "content": "".join(selected),
        "truncated": end_index < total,
    }


def searchText(
    query: str,
    path: str = ".",
    glob: str | None = None,
    ignoreCase: bool = False,
    useRegex: bool = False,
    limit: int = 200,
) -> dict[str, Any]:
    """Search text using rg when available, falling back to Python file scanning."""
    if not query:
        raise ValueError("query must not be empty")
    root = Path(path).expanduser().resolve()
    max_items = max(1, int(limit))
    if shutil.which("rg"):
        return _searchWithRg(query, root, glob, ignoreCase, useRegex, max_items)
    return _searchWithPython(query, root, glob, ignoreCase, useRegex, max_items)


def searchFiles(
    pattern: str,
    path: str = ".",
    recursive: bool = True,
    ignoreCase: bool = True,
    mode: str = "contains",
    limit: int = 200,
) -> dict[str, Any]:
    """Search file and directory names under a path."""
    if not pattern:
        raise ValueError("pattern must not be empty")
    search_mode = _normalizeSearchFilesMode(mode)
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(str(root))

    max_items = max(1, int(limit))
    needle = pattern.lower() if ignoreCase else pattern
    regex = re.compile(pattern, re.IGNORECASE if ignoreCase else 0) if search_mode == "regex" else None
    if root.is_file():
        candidates = [root]
        base = root.parent
    elif recursive:
        candidates = list(root.rglob("*"))
        base = root
    else:
        candidates = list(root.iterdir())
        base = root

    matches = []
    for item in sorted(candidates, key=lambda value: str(value).lower()):
        name = item.name
        haystack = name.lower() if ignoreCase else name
        if not _fileNameMatches(name, haystack, needle, pattern, search_mode, bool(ignoreCase), regex):
            continue
        matches.append(_entry(item, base))
        if len(matches) >= max_items:
            break

    return {
        "success": True,
        "pattern": pattern,
        "mode": search_mode,
        "path": str(root),
        "matched": bool(matches),
        "matches": matches,
        "truncated": len(matches) >= max_items,
    }


def writeFile(
    path: str,
    content: str,
    createParents: bool = False,
    mode: str = "overwrite",
) -> dict[str, Any]:
    """Write text content to a file using overwrite or append mode."""
    target = Path(path).expanduser().resolve()
    if createParents:
        target.parent.mkdir(parents=True, exist_ok=True)
    if not target.parent.exists():
        raise FileNotFoundError(str(target.parent))
    write_mode = _normalizeWriteMode(mode)
    if write_mode == "append":
        with target.open("a", encoding="utf-8") as file:
            file.write(content)
    else:
        target.write_text(content, encoding="utf-8")
    return {
        "success": True,
        "path": str(target),
        "mode": write_mode,
        "bytesWritten": len(content.encode("utf-8")),
    }


def writeFiles(files: list[dict[str, Any]], createParents: bool = True) -> dict[str, Any]:
    """Write multiple files, returning per-file results."""
    results = []
    for item in files:
        try:
            item_create_parents = bool(item.get("createParents", createParents))
            result = writeFile(
                path=str(item["path"]),
                content=str(item.get("content", "")),
                createParents=item_create_parents,
                mode=str(item.get("mode", "overwrite")),
            )
            results.append(result)
        except Exception as exc:
            results.append(_itemError(item.get("path"), exc))
    return _batchResult(results)


def readFiles(files: list[dict[str, Any]]) -> dict[str, Any]:
    """Read multiple files, returning per-file results."""
    results = []
    for item in files:
        try:
            result = readFile(
                path=str(item["path"]),
                offset=int(item.get("offset", 0)),
                limitBytes=int(item.get("limitBytes", 65536)),
                lineStart=item.get("lineStart"),
                lineLimit=item.get("lineLimit"),
            )
            results.append(result)
        except Exception as exc:
            results.append(_itemError(item.get("path"), exc))
    return _batchResult(results)


def statPaths(paths: list[str]) -> dict[str, Any]:
    """Return metadata for multiple paths."""
    results = []
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            results.append({"success": False, "path": str(path), "exists": False})
            continue
        try:
            item = _entry(path, path.parent)
            item["success"] = True
            item["exists"] = True
            results.append(item)
        except Exception as exc:
            results.append(_itemError(str(path), exc))
    return _batchResult(results)


def searchTexts(
    queries: list[str],
    path: str = ".",
    glob: str | None = None,
    ignoreCase: bool = False,
    useRegex: bool = False,
    limitPerQuery: int = 100,
) -> dict[str, Any]:
    """Run multiple text searches under one path."""
    results = []
    for query in queries:
        try:
            results.append(
                searchText(
                    query,
                    path=path,
                    glob=glob,
                    ignoreCase=ignoreCase,
                    useRegex=useRegex,
                    limit=limitPerQuery,
                )
            )
        except Exception as exc:
            results.append(_itemError(query, exc))
    return _batchResult(results)


def replaceText(
    path: str,
    oldText: str,
    newText: str,
    replaceAll: bool = False,
) -> dict[str, Any]:
    """Replace exact text in a file, refusing ambiguous single replacements."""
    if not oldText:
        raise ValueError("oldText must not be empty")
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(str(target))
    _ensureTextFile(target)

    content = target.read_text(encoding="utf-8", errors="replace")
    count = content.count(oldText)
    if count == 0:
        raise ValueError("oldText was not found")
    if count > 1 and not replaceAll:
        raise ValueError("oldText appears multiple times; set replaceAll=true to replace all matches")

    max_replacements = -1 if replaceAll else 1
    updated = content.replace(oldText, newText, max_replacements)
    target.write_text(updated, encoding="utf-8")
    replacements = count if replaceAll else 1
    return {
        "success": True,
        "path": str(target),
        "replacements": replacements,
        "bytesWritten": len(updated.encode("utf-8")),
    }


def replaceRange(path: str, lineStart: int, lineEnd: int, newText: str) -> dict[str, Any]:
    """Replace an inclusive one-based line range with new text."""
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(str(target))
    _ensureTextFile(target)

    start = max(1, int(lineStart))
    end = max(start, int(lineEnd))
    lines = target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    if start > len(lines) + 1:
        raise ValueError("lineStart is beyond the end of the file")

    start_index = start - 1
    end_index = min(end, len(lines))
    replacement = _textToLines(newText)
    updated_lines = lines[:start_index] + replacement + lines[end_index:]
    updated = "".join(updated_lines)
    target.write_text(updated, encoding="utf-8")
    return {
        "success": True,
        "path": str(target),
        "lineStart": start,
        "lineEnd": end,
        "oldLineCount": end_index - start_index,
        "newLineCount": len(replacement),
        "changed": True,
        "bytesWritten": len(updated.encode("utf-8")),
    }


def insertText(
    path: str,
    anchorText: str,
    newText: str,
    position: str = "after",
    occurrence: int = 1,
) -> dict[str, Any]:
    """Insert text before or after the Nth occurrence of an anchor string."""
    if not anchorText:
        raise ValueError("anchorText must not be empty")
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(str(target))
    _ensureTextFile(target)

    normalized_position = _normalizePosition(position)
    content = target.read_text(encoding="utf-8", errors="replace")
    occurrence_index = max(1, int(occurrence))
    anchor_index = _nthIndex(content, anchorText, occurrence_index)
    if anchor_index < 0:
        raise ValueError("anchorText occurrence was not found")
    insert_at = anchor_index if normalized_position == "before" else anchor_index + len(anchorText)
    updated = content[:insert_at] + newText + content[insert_at:]
    target.write_text(updated, encoding="utf-8")
    return {
        "success": True,
        "path": str(target),
        "position": normalized_position,
        "occurrence": occurrence_index,
        "insertOffset": insert_at,
        "bytesWritten": len(updated.encode("utf-8")),
    }


def replaceRegex(
    path: str,
    pattern: str,
    replacement: str,
    replaceAll: bool = False,
    flags: str = "",
) -> dict[str, Any]:
    """Replace text with a regular expression."""
    if not pattern:
        raise ValueError("pattern must not be empty")
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(str(target))
    _ensureTextFile(target)

    regex = re.compile(pattern, _regexFlags(flags))
    content = target.read_text(encoding="utf-8", errors="replace")
    count = 0 if replaceAll else 1
    updated, replacements = regex.subn(replacement, content, count=count)
    if replacements == 0:
        raise ValueError("pattern did not match")
    target.write_text(updated, encoding="utf-8")
    return {
        "success": True,
        "path": str(target),
        "replacements": replacements,
        "bytesWritten": len(updated.encode("utf-8")),
    }


def editBatch(
    edits: list[dict[str, Any]],
    stopOnFailure: bool = False,
    dryRun: bool = False,
) -> dict[str, Any]:
    """Run or validate multiple text edits sequentially with per-edit results."""
    results = []
    for index, edit in enumerate(edits):
        edit_type = str(edit.get("type", "")).strip()
        try:
            if dryRun:
                result = _previewEdit(edit_type, edit)
            elif edit_type == "replaceText":
                result = replaceText(
                    path=str(edit["path"]),
                    oldText=str(edit["oldText"]),
                    newText=str(edit["newText"]),
                    replaceAll=bool(edit.get("replaceAll", False)),
                )
            elif edit_type == "replaceRange":
                result = replaceRange(
                    path=str(edit["path"]),
                    lineStart=int(edit["lineStart"]),
                    lineEnd=int(edit["lineEnd"]),
                    newText=str(edit["newText"]),
                )
            elif edit_type == "insertText":
                result = insertText(
                    path=str(edit["path"]),
                    anchorText=str(edit["anchorText"]),
                    newText=str(edit["newText"]),
                    position=str(edit.get("position", "after")),
                    occurrence=int(edit.get("occurrence", 1)),
                )
            elif edit_type == "replaceRegex":
                result = replaceRegex(
                    path=str(edit["path"]),
                    pattern=str(edit["pattern"]),
                    replacement=str(edit["replacement"]),
                    replaceAll=bool(edit.get("replaceAll", False)),
                    flags=str(edit.get("flags", "")),
                )
            else:
                raise ValueError("edit type must be one of: replaceText, replaceRange, insertText, replaceRegex")
            results.append({"index": index, "type": edit_type, **result})
        except Exception as exc:
            item = _itemError(edit.get("path"), exc)
            item["index"] = index
            item["type"] = edit_type or None
            results.append(item)
            if stopOnFailure:
                break
    result = _batchResult(results)
    result["dryRun"] = dryRun
    result["stopOnFailure"] = stopOnFailure
    result["stoppedEarly"] = bool(stopOnFailure and result["failed"] > 0 and len(results) < len(edits))
    return result


def applyPatch(patch: str, cwd: str = ".") -> dict[str, Any]:
    """Apply a unified diff patch in the given working directory."""
    if not patch.strip():
        raise ValueError("patch must not be empty")

    workdir = Path(cwd).expanduser().resolve()
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as file:
        file.write(patch)
        patch_path = file.name

    try:
        result = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", patch_path],
            cwd=str(workdir),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
            shell=False,
        )
        return {
            "success": result.returncode == 0,
            "command": ["git", "apply", "--whitespace=nowarn"],
            "cwd": str(workdir),
            "returnCode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    finally:
        try:
            os.unlink(patch_path)
        except OSError:
            pass


def formatPatchDiagnostics(patch: str, stderr: str = "") -> dict[str, Any]:
    """Return simple diagnostics for a failed unified diff patch."""
    text = stderr or ""
    suggestions = []
    likely_cause = "unknown"
    suggested_tool = "applyPatch"
    if "corrupt patch at line" in text:
        likely_cause = "corrupt_hunk"
        suggested_tool = "replaceRange"
        suggestions.append("Use replaceRange or editBatch for small edits, or fix the hunk header line counts.")
    if "No valid patches in input" in text:
        likely_cause = "invalid_patch_format"
        suggested_tool = "format_unified_diff"
        suggestions.append("Use a standard unified diff with ---/+++ file headers and @@ hunk headers.")
    if "patch does not apply" in text:
        likely_cause = "stale_context"
        suggested_tool = "replaceRange"
        suggestions.append("Re-read the target file and regenerate the patch against current content.")
    if not suggestions:
        suggestions.append("Verify file paths, hunk headers, and unchanged context lines.")
    reported_line = _reportedPatchLine(text)
    return {
        "success": True,
        "hasPatchHeaders": "--- " in patch and "+++ " in patch,
        "hunkCount": _countPatchHunks(patch),
        "reportedLine": reported_line,
        "likelyCause": likely_cause,
        "suggestedTool": suggested_tool,
        "stderr": stderr,
        "suggestions": suggestions,
    }


def createDirectory(path: str, parents: bool = True) -> dict[str, Any]:
    """Create a directory."""
    target = Path(path).expanduser().resolve()
    existed_before = target.exists()
    target.mkdir(parents=parents, exist_ok=parents)
    return {
        "success": True,
        "path": str(target),
        "existedBefore": existed_before,
        "changed": not existed_before,
    }


def deletePath(path: str, recursive: bool = False) -> dict[str, Any]:
    """Delete a file, symlink, or directory."""
    target = Path(path).expanduser().resolve()
    existed_before = target.exists() or target.is_symlink()
    if not existed_before:
        return {"success": True, "path": str(target), "existedBefore": False, "changed": False}
    if target.is_dir() and not target.is_symlink():
        if not recursive:
            target.rmdir()
        else:
            shutil.rmtree(target)
    else:
        target.unlink()
    return {
        "success": True,
        "path": str(target),
        "existedBefore": existed_before,
        "changed": True,
    }


def movePath(source: str, destination: str) -> dict[str, Any]:
    """Move or rename a file or directory."""
    src = Path(source).expanduser().resolve()
    dest = Path(destination).expanduser().resolve()
    if not src.exists() and not src.is_symlink():
        raise FileNotFoundError(str(src))
    existed_before = dest.exists() or dest.is_symlink()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    return {
        "success": True,
        "source": str(src),
        "destination": str(dest),
        "destinationExistedBefore": existed_before,
        "changed": True,
    }


def copyPath(source: str, destination: str, overwrite: bool = False) -> dict[str, Any]:
    """Copy a file or directory."""
    src = Path(source).expanduser().resolve()
    dest = Path(destination).expanduser().resolve()
    if not src.exists() and not src.is_symlink():
        raise FileNotFoundError(str(src))
    existed_before = dest.exists() or dest.is_symlink()
    if existed_before and not overwrite:
        raise FileExistsError(str(dest))
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir() and not src.is_symlink():
        if existed_before:
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
    return {
        "success": True,
        "source": str(src),
        "destination": str(dest),
        "destinationExistedBefore": existed_before,
        "changed": True,
    }


def _iterFiles(root: Path, recursive: bool, maxDepth: int, includeHidden: bool):
    if not recursive:
        for item in sorted(root.iterdir(), key=lambda value: value.name.lower()):
            if includeHidden or not item.name.startswith("."):
                yield item
        return

    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.relative_to(root).parts)
        if depth >= maxDepth:
            dirs[:] = []
        if not includeHidden:
            dirs[:] = [name for name in dirs if not name.startswith(".")]
            files = [name for name in files if not name.startswith(".")]
        for dirname in sorted(dirs, key=str.lower):
            yield current_path / dirname
        for filename in sorted(files, key=str.lower):
            yield current_path / filename


def _entry(path: Path, base: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.relative_to(base)),
        "absolutePath": str(path),
        "type": "directory" if path.is_dir() else "file",
        "sizeBytes": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }


def _normalizeSortBy(sortBy: str) -> str:
    value = str(sortBy).strip().lower()
    allowed = {"path", "name", "mtime", "size"}
    if value not in allowed:
        raise ValueError("sortBy must be one of: path, name, mtime, size")
    return value


def _normalizeSortOrder(sortOrder: str) -> str:
    value = str(sortOrder).strip().lower()
    if value not in {"asc", "desc"}:
        raise ValueError("sortOrder must be one of: asc, desc")
    return value


def _normalizeSearchFilesMode(mode: str) -> str:
    value = str(mode).strip().lower()
    if value not in {"contains", "glob", "regex"}:
        raise ValueError("mode must be one of: contains, glob, regex")
    return value


def _fileNameMatches(
    name: str,
    haystack: str,
    needle: str,
    pattern: str,
    mode: str,
    ignoreCase: bool,
    regex: re.Pattern[str] | None,
) -> bool:
    if mode == "regex":
        return bool(regex and regex.search(name))
    if mode == "glob":
        candidate = name.lower() if ignoreCase else name
        glob_pattern = pattern.lower() if ignoreCase else pattern
        return fnmatch.fnmatchcase(candidate, glob_pattern)
    return needle in haystack


def _sortKey(entry: dict[str, Any], sortBy: str):
    if sortBy == "name":
        return Path(entry["path"]).name.lower()
    if sortBy == "mtime":
        return entry["mtime"]
    if sortBy == "size":
        return entry["sizeBytes"]
    return entry["path"].lower()


def _normalizeWriteMode(mode: str) -> str:
    value = str(mode).strip().lower()
    if value not in {"overwrite", "append"}:
        raise ValueError("mode must be one of: overwrite, append")
    return value


def _ensureTextFile(path: Path) -> None:
    with path.open("rb") as file:
        sample = file.read(4096)
    if _looksBinary(sample):
        raise ValueError("binary file cannot be read as text")


def _looksBinary(sample: bytes) -> bool:
    return b"\0" in sample


def _searchWithRg(
    query: str,
    root: Path,
    glob: str | None,
    ignoreCase: bool,
    useRegex: bool,
    limit: int,
) -> dict[str, Any]:
    command = ["rg", "--line-number", "--no-heading", "--color", "never"]
    if not useRegex:
        command.append("--fixed-strings")
    if ignoreCase:
        command.append("--ignore-case")
    if glob:
        command.extend(["--glob", glob])
    command.extend([query, str(root)])
    result = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
        shell=False,
    )
    matches = []
    for line in result.stdout.splitlines():
        parsed = _parseRgLine(line)
        if parsed:
            matches.append(parsed)
        if len(matches) >= limit:
            break
    return {
        "success": result.returncode in (0, 1),
        "query": query,
        "path": str(root),
        "matched": bool(matches),
        "useRegex": useRegex,
        "matches": matches,
        "truncated": len(matches) >= limit,
        "returnCode": result.returncode,
        "stderr": result.stderr,
    }


def _parseRgLine(line: str) -> dict[str, Any] | None:
    first = line.find(":")
    if first < 0:
        return None
    second = line.find(":", first + 1)
    if second < 0:
        return None
    try:
        line_number = int(line[first + 1 : second])
    except ValueError:
        return None
    return {
        "path": line[:first],
        "lineNumber": line_number,
        "line": line[second + 1 :],
    }


def _searchWithPython(
    query: str,
    root: Path,
    glob: str | None,
    ignoreCase: bool,
    useRegex: bool,
    limit: int,
) -> dict[str, Any]:
    needle = query.lower() if ignoreCase else query
    regex = re.compile(query, re.IGNORECASE if ignoreCase else 0) if useRegex else None
    matches = []
    paths = [root] if root.is_file() else root.rglob(glob or "*")
    for item in paths:
        if not item.is_file():
            continue
        try:
            with item.open("rb") as file:
                sample = file.read(4096)
                if _looksBinary(sample):
                    continue
                file.seek(0)
                for line_number, raw_line in enumerate(file, start=1):
                    line = raw_line.decode("utf-8", errors="replace").rstrip("\n")
                    haystack = line.lower() if ignoreCase else line
                    matched = bool(regex.search(line)) if regex else needle in haystack
                    if matched:
                        matches.append(
                            {
                                "path": str(item),
                                "lineNumber": line_number,
                                "line": line,
                            }
                        )
                    if len(matches) >= limit:
                        return {
                            "success": True,
                            "query": query,
                            "path": str(root),
                            "matched": True,
                            "useRegex": useRegex,
                            "matches": matches,
                            "truncated": True,
                        }
        except OSError:
            continue
    return {
        "success": True,
        "query": query,
        "path": str(root),
        "matched": bool(matches),
        "useRegex": useRegex,
        "matches": matches,
        "truncated": False,
    }


def _batchResult(results: list[dict[str, Any]]) -> dict[str, Any]:
    succeeded = sum(1 for item in results if item.get("success") is True)
    return {
        "success": succeeded == len(results),
        "total": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "results": results,
    }


def _itemError(path: Any, exc: Exception) -> dict[str, Any]:
    return {
        "success": False,
        "path": str(path) if path is not None else None,
        "errorCode": exc.__class__.__name__,
        "errorMessage": str(exc),
    }


def _previewEdit(edit_type: str, edit: dict[str, Any]) -> dict[str, Any]:
    if edit_type == "replaceText":
        target = _textEditTarget(edit)
        old_text = str(edit["oldText"])
        if not old_text:
            raise ValueError("oldText must not be empty")
        content = target.read_text(encoding="utf-8", errors="replace")
        count = content.count(old_text)
        if count == 0:
            raise ValueError("oldText was not found")
        if count > 1 and not bool(edit.get("replaceAll", False)):
            raise ValueError("oldText appears multiple times; set replaceAll=true to replace all matches")
        return {
            "success": True,
            "path": str(target),
            "dryRun": True,
            "wouldChange": True,
            "matches": count,
            "replacements": count if bool(edit.get("replaceAll", False)) else 1,
        }

    if edit_type == "replaceRange":
        target = _textEditTarget(edit)
        start = max(1, int(edit["lineStart"]))
        end = max(start, int(edit["lineEnd"]))
        total = len(target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True))
        if start > total + 1:
            raise ValueError("lineStart is beyond the end of the file")
        return {
            "success": True,
            "path": str(target),
            "dryRun": True,
            "wouldChange": True,
            "lineStart": start,
            "lineEnd": end,
            "oldLineCount": min(end, total) - (start - 1),
            "newLineCount": len(_textToLines(str(edit["newText"]))),
        }

    if edit_type == "insertText":
        target = _textEditTarget(edit)
        anchor_text = str(edit["anchorText"])
        if not anchor_text:
            raise ValueError("anchorText must not be empty")
        content = target.read_text(encoding="utf-8", errors="replace")
        occurrence = max(1, int(edit.get("occurrence", 1)))
        anchor_index = _nthIndex(content, anchor_text, occurrence)
        if anchor_index < 0:
            raise ValueError("anchorText occurrence was not found")
        position = _normalizePosition(str(edit.get("position", "after")))
        insert_at = anchor_index if position == "before" else anchor_index + len(anchor_text)
        return {
            "success": True,
            "path": str(target),
            "dryRun": True,
            "wouldChange": True,
            "position": position,
            "occurrence": occurrence,
            "insertOffset": insert_at,
        }

    if edit_type == "replaceRegex":
        target = _textEditTarget(edit)
        pattern = str(edit["pattern"])
        if not pattern:
            raise ValueError("pattern must not be empty")
        regex = re.compile(pattern, _regexFlags(str(edit.get("flags", ""))))
        content = target.read_text(encoding="utf-8", errors="replace")
        matches = len(regex.findall(content))
        if matches == 0:
            raise ValueError("pattern did not match")
        return {
            "success": True,
            "path": str(target),
            "dryRun": True,
            "wouldChange": True,
            "matches": matches,
            "replacements": matches if bool(edit.get("replaceAll", False)) else 1,
        }

    raise ValueError("edit type must be one of: replaceText, replaceRange, insertText, replaceRegex")


def _textEditTarget(edit: dict[str, Any]) -> Path:
    target = Path(str(edit["path"])).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(str(target))
    _ensureTextFile(target)
    return target


def _textToLines(text: str) -> list[str]:
    if text == "":
        return []
    return text.splitlines(keepends=True)


def _normalizePosition(position: str) -> str:
    value = str(position).strip().lower()
    if value not in {"before", "after"}:
        raise ValueError("position must be one of: before, after")
    return value


def _nthIndex(text: str, needle: str, occurrence: int) -> int:
    start = 0
    for _ in range(occurrence):
        index = text.find(needle, start)
        if index < 0:
            return -1
        start = index + len(needle)
    return index


def _regexFlags(flags: str) -> int:
    value = 0
    for flag in str(flags).lower():
        if flag == "i":
            value |= re.IGNORECASE
        elif flag == "m":
            value |= re.MULTILINE
        elif flag == "s":
            value |= re.DOTALL
        elif flag in {" ", ","}:
            continue
        else:
            raise ValueError("flags may contain only i, m, and s")
    return value


def _countPatchHunks(patch: str) -> int:
    hunk_header = re.compile(r"^@@\s+-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s+@@")
    return sum(1 for line in patch.splitlines() if hunk_header.match(line))


def _reportedPatchLine(stderr: str) -> int | None:
    match = re.search(r"corrupt patch at line\s+(\d+)", stderr, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))
