---
id: port-mcp-server-to-sdk-2x-api
type: backlog_item
title: "Port build_sdk_server() to the mcp SDK 2.x API and lift the <2.0.0 pin"
kind: tech_debt
status: proposed
priority: medium
effort: M
created: "2026-09-17"
tags: [mcp, dependencies, sdk, upgrade, pin-removal]
links:
- target: unbounded-dependency-ranges-break-ci-on-upstream-releases
  relation: related
  kb: pyrite
---

## Problem

`pyproject.toml` pins `mcp>=1.0.0,<2.0.0`. That pin is a **stopgap**, added
in PR #3 (contributed by AsyncLegs / Ruslan Terekhov, merged 2026-09-17) to
stop a fresh install resolving the 2.x SDK, where every MCP request 500s:

```
File "pyrite/server/mcp_server.py", line 1702, in build_sdk_server
    @sdk.list_tools()
     ^^^^^^^^^^^^^^
AttributeError: 'Server' object has no attribute 'list_tools'
```

The pin was the right immediate fix — an unbounded `mcp>=1.0.0` was
resolving **2.2.0** in CI by the time it was filed, two majors past what the
code supports — but it freezes pyrite on a major version the ecosystem is
moving off.

## Scope

`build_sdk_server()` in `pyrite/server/mcp_server.py` uses the 1.x low-level
`Server` decorator API throughout. Every one of these call sites needs a 2.x
equivalent:

| Line | 1.x API |
|---|---|
| 1683 | `from mcp.server import Server` |
| 1697 | `sdk = Server(f"pyrite-{self.tier}")` |
| 1702 | `@sdk.list_tools()` |
| 1713 | `@sdk.call_tool()` |
| 1722 | `@sdk.list_prompts()` |
| 1740 | `@sdk.get_prompt()` |
| 1757 | `@sdk.list_resources()` |
| 1769 | `@sdk.list_resource_templates()` |
| 1781 | `@sdk.read_resource()` |
| 1802 | `from mcp.server.stdio import stdio_server` |

Also in scope: `mcp.types` imports (line 1684), and the SSE transport
mounting in `pyrite/server/mcp_routes.py`, whose `root_path` behavior PR #3
also corrected — confirm 2.x has the same `root_path + endpoint`
concatenation semantics before assuming the `/messages/` fix carries over.

## Fix

1. Read the 2.x migration guide and establish what replaced the low-level
   `Server` decorator API. Do not guess from the AttributeError.
2. Port `build_sdk_server()` and the stdio entry point.
3. Verify the SSE transport end-to-end against a real client (PR #3's
   verification bar: `claude mcp list` shows `Connected`, and a tool call
   round-trips). The four `test_mcp_*` unit tests are necessary but not
   sufficient — they passed while the transport was broken in deployment.
4. Lift the pin to `mcp>=2.0.0` (or a bounded 2.x range — see the related
   ticket on unbounded ranges; do not go back to unbounded).
5. Confirm the four tests that the pin currently keeps green stay green:
   `test_mcp_prompts::test_build_sdk_server_creates_server`,
   `test_mcp_routes::TestBuildSDKServerClientID` (x2),
   `test_mcp_server::TestMCPProtocol::test_build_sdk_server`.

## Why this is medium and not high

The pin works and nothing is currently broken by it. The cost is deferred:
pyrite cannot adopt 2.x features, and any dependency that itself requires
`mcp>=2` will conflict. Raise priority if a pilot peer or contributor hits
that conflict.

## Acceptance criteria

- `build_sdk_server()` runs on the 2.x SDK with no 1.x API references left
  in `mcp_server.py`.
- The `<2.0.0` ceiling is removed from `pyproject.toml`.
- SSE transport verified against a real MCP client, not just unit tests.
- A fresh `pip install -e ".[all]"` in a clean environment resolves a 2.x
  `mcp` and the MCP test suite passes.
