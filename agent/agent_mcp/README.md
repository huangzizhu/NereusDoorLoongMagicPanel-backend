# Agent Core MCP Server

Standalone stdio MCP server for coding-agent basics.

## Scope

This server exposes only project-coding tools:

- Workspace: `getWorkspaceContext`, `summarizeWorkspace`, `summarizeFile`
- File listing/search: `listFiles`, `searchFiles`, `searchText`, `searchTexts`
- File reading/stat: `readFile`, `readFiles`, `statPaths`
- File writing/editing: `writeFile`, `writeFiles`, `replaceText`,
  `replaceRange`, `insertText`, `replaceRegex`, `editBatch`, `applyPatch`,
  `formatPatchDiagnostics`
- Path operations: `createDirectory`, `copyPath`, `movePath`, `deletePath`
- Git/project workflow: `getGitStatus`, `getGitDiff`,
  `listGitChangedFiles`, `detectProjectCommands`, `runProjectCheck`
- Command/error helpers: `runCommand`, `runShellCommand`,
  `getRecentCommandResults`,
  `explainToolError`

It intentionally does not register operations tools, privileged-agent tools,
sandboxing, approval handling, or policy guardrails. Those controls are expected
to live in the external safety layer.

## Tool Notes

- `getWorkspaceContext` accepts `path`, so agents can inspect temp projects or
  monorepo subdirectories.
- `readFile` supports byte ranges with `offset`/`limitBytes` and line ranges
  with `lineStart`/`lineLimit`.
- `readFiles`, `writeFiles`, `searchTexts`, and `statPaths` are batch helpers.
  Each item returns its own result so one failure does not hide other results.
- `writeFile` supports `mode="overwrite"` and `mode="append"`.
- `replaceText` is intended for small exact edits. It refuses ambiguous single
  replacements when `oldText` appears multiple times unless `replaceAll=true`.
- `replaceRange`, `insertText`, and `replaceRegex` are agent-friendly edit
  tools for cases where unified diff hunks are easy to get wrong.
- `editBatch` runs multiple `replaceText`, `replaceRange`, `insertText`, and
  `replaceRegex` edits sequentially. It does not roll back prior successful
  edits if a later edit fails.
- `editBatch(stopOnFailure=true)` stops after the first failed edit.
  `editBatch(dryRun=true)` validates matches and line ranges without writing
  files.
- `applyPatch` accepts `cwd`, so agents can patch temporary projects or
  monorepo subdirectories.
- Prefer editing tools in this order for small changes: `replaceText`,
  `replaceRegex`, `replaceRange`, `insertText`, then `editBatch` for multiple
  edits. Use `applyPatch` for complex unified diffs.
- `copyPath` and `movePath` create missing destination parent directories.
- `runCommand.maxOutputBytes` is a byte limit applied separately to stdout and
  stderr. Results include original and returned byte counts plus per-stream
  truncation flags.
- Prefer `runCommand` for normal commands. It takes argv such as
  `["python", "-m", "unittest", "discover", "-s", "tests"]` and does not
  interpret shell syntax.
- Use `runShellCommand` only when shell behavior is actually needed, such as
  pipes (`rg foo | head`), redirects (`> out.txt`), globs (`*.py`), variables,
  command substitution, or `&&`/`||` chains. It runs through `bash -lc` and is
  intentionally marked as an advanced shell tool. Command results include
  `advanced=false` for `runCommand` and `advanced=true` for `runShellCommand`.
- `getRecentCommandResults` returns command summaries from the current MCP
  process memory only; it does not persist history.
- `searchText` returns `success=true` with `returnCode=1` and empty `matches`
  when no result is found. It also returns `matched=false`.
- `searchText` uses literal matching by default. Set `useRegex=true` for regular
  expression searches.
- `searchFiles` supports `mode="contains"`, `mode="glob"`, and `mode="regex"`.
  The default is `contains`; use `mode="glob"` for patterns such as `*.py`.
- `runProjectCheck` uses detected commands from project markers unless an
  explicit argv-style command is provided. Its top-level `success` means the
  project check passed; nested `result.success` means the command process ran
  and produced a result.

## Run

From the project root:

```bash
python -m agent.agent_mcp
```

From `ndlmpanel_agent/`:

```bash
python -m agent_mcp
```

## MCP Client Shape

```json
{
  "mcpServers": {
    "ndlmpanel-agent-core": {
      "command": "python",
      "args": ["-m", "agent.agent_mcp"],
      "cwd": "/home/he/workspace/python/NereusDoorLoongMagicPanel-backend"
    }
  }
}
```
