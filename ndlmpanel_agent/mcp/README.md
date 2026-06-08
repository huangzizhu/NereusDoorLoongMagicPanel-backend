# NDLM Panel MCP Server

This package provides the standalone MCP server for NDLM Panel Agent.

## Current Phase

- Transport: `stdio`
- Protocol methods: `initialize`, `notifications/initialized`, `ping`, `tools/list`, `tools/call`
- Tool source: `utils.toolFunction`
- Legacy `ndlmpanel_agent/plugins` tools are not registered
- HTTP transport is reserved for the next phase

## Run

From the project root:

```bash
python -m ndlmpanel_agent.mcp
```

From `ndlmpanel_agent/`:

```bash
python -m mcp
```

Explicit transport selection:

```bash
python -m ndlmpanel_agent.mcp --transport stdio
```

## Agent Configuration Shape

Most MCP clients need a command plus args:

```json
{
  "mcpServers": {
    "ndlmpanel-agent": {
      "command": "python",
      "args": ["-m", "ndlmpanel_agent.mcp"],
      "cwd": "/home/he/workspace/python/NereusDoorLoongMagicPanel-backend"
    }
  }
}
```

## Tool Policy

The first phase exposes a curated operations tool set: filesystem, system
observation, process diagnostics, network diagnostics, logs, systemd, firewall,
Docker, Nginx, and database status tools.

`executeCommand` is exposed only in the stdio tool set. It accepts argv-style
commands as a list and does not use shell expansion.

## Agent-Optimized Tools

Prefer these wrapper tools for agent workflows:

- `listProcessesBrief`: compact process list with `limit`, `sortBy`, `keyword`,
  and optional command text.
- `getProcessAnomalies`: compact zombie-process query. Set
  `includeReparented=true` only when inspecting PID 1 reparented processes.
- `getDockerContainerSummary`: compact Docker container summary instead of full
  `docker inspect`.
- `testNginxConfigPrivileged`: run `nginx -t` through the privileged agent.
- `listFirewallPortsPrivileged`: list firewall rules through the privileged
  agent.
- `addFirewallPortPrivileged`: add an allow firewall port rule through the
  privileged agent.
- `manageSystemServicePrivileged`: inspect services directly and change allowed
  services through the privileged agent.

Tools ending in `Privileged` use `NDLM_PRIVILEGED_AGENT_SOCKET`, defaulting to
`/run/ndlmpanel/privileged-agent.sock`. If the privileged agent is unavailable,
the MCP tool result is an error JSON payload with `requiresPrivilege=true` and
`backend="privileged_agent"`.
