#!/usr/bin/env python3
"""
Produces an action_ref for a real `prepare_action` (supply) tool call
against Aave's official MCP server (https://mcp.aave.com, the server
aave/skills' plugin.mcp.json points agents at), following action-ref-v1
(argentum-core, JCS RFC 8785 + SHA-256) byte-for-byte, and emits the
artifacts needed to anchor + independently verify it.

PROVENANCE: unlike the companion worked examples for Tether's WDK and
PayPal's agent-toolkit (which model params/result from the toolkits' own
public npm source, since no running server was available to call), the
`confirmation` block below is NOT modeled — it is the real, live response
`prepare_action` returned for a real tools/call JSON-RPC request against
mcp.aave.com on 2026-11-06T20:43:32.000Z, for a real USDC v4 market on
Base mainnet (reserveId from a real get_markets call in the same
session), using the "dEaDbEEF" synthetic placeholder sender address
(same obviously-fake convention as wdk-action-ref-anchor) sized at an
amount (0.005 USDC) chosen because that address happened to hold exactly
0.01 USDC in dust at call time -- not because it is a wallet we control.
No approval was signed and no transaction was broadcast: `prepare_action`
itself never sends anything (readOnlyHint / destructiveHint: false, per
the server's own tools/list), so making this call cost nothing and
touched no funds. The `result` block (what get_transaction_processed
would report) IS modeled -- see the note at that assignment below.
"""
import hashlib
import json
import os
import sys

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "artifacts"
os.makedirs(OUT_DIR, exist_ok=True)


def jcs(obj):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


# --- 1. The four required action-ref-v1 preimage fields --------------------
# Per argentum-core/docs/spec/action-ref.md: only these four fields enter the
# hash. action_type mirrors the registered MCP tool name ("prepare_action");
# scope carries the server + tool + action + version context (mcp.aave.com
# serves one endpoint for v3 and v4, selected per call), terminal executing
# agent is this worked example's synthetic identity.
timestamp = "2026-11-06T20:43:32.000Z"
preimage = {
    "agent_id": "worked-example.aave-action-ref-anchor",
    "action_type": "aave.mcp.prepare_action",
    "scope": "aave:mcp:server:mcp.aave.com:tool:prepare_action:action:supply:version:v4",
    "timestamp": timestamp,
}
jcs_payload = jcs(preimage)
action_ref = sha256_hex(jcs_payload)

# --- 2. Additive envelope fields — aave MCP-specific context ---------------
# These do NOT enter the action_ref hash (per action-ref-v1: only the 4
# preimage fields are hashed). They travel alongside as declared context a
# downstream verifier can check independently:
#   params       — the prepare_action tool's own declared inputSchema
#                  (action, version, sender, reserveId, amount), exactly as
#                  sent in the real tools/call request below.
#   confirmation — the unsigned transaction prepare_action itself returned
#                  (its `data.originalTransaction`, the supply call on the
#                  Base USDC v4 Spoke -- `to`, `data`, `value`, `chainId`,
#                  and the `operations` array get_transaction_processed
#                  requires) -- REAL, captured live, not modeled. This is
#                  the tool's own pre-execution accountability primitive:
#                  what the user's wallet would sign, exactly as it would
#                  see it. It is PRE-execution (nothing was signed or
#                  broadcast), same role as wdk-action-ref-anchor's
#                  confirmation_digest, not a post-execution record a
#                  third party could check later.
#   result       — see the note immediately below: modeled, not live.
#
# Real values captured from mcp.aave.com (session c055505a-424e-4f77-9f28-
# 501a035e1395, request id 7, response Date header
# "Fri, 06 Nov 2026 20:43:32 GMT"):
#   get_markets({"symbols":["USDC"],"version":"v4"}) -> the Base mainnet
#   (chainId 8453) USDC v4 row, reserveId
#   "ODQ1Mzo6MHgxNzkwNURiMGU0QTM1MTQ0Njc1Mzk5NTZjMDg0MTgwNjE2QUU3QjhEOjo3"
#   (opaque, per the server's own schema description -- "cannot be
#   constructed or recalled").
#
# The sender address is the same obviously-synthetic "dEaDbEEF" burn
# address wdk-action-ref-anchor uses -- not a wallet we control, never
# funded by us. It happened to already hold 0.01 USDC in dust on Base at
# call time (anyone can check: it is a well-known burn address other
# people send dust to), which is why the amount below (0.005) is sized
# under that, rather than a rounder number -- prepare_action checks the
# sender's real balance even to build an unsigned tx, so a larger amount
# was rejected with INSUFFICIENT_BALANCE (see PROVENANCE.md for the
# rejected attempt). Below 0.01 USDC the Base USDC contract (not the
# sender) still requires an ERC-20 approval before the supply can run,
# which is exactly the real response captured: an Erc20ApprovalRequired
# envelope carrying both the approval tx (`byTransaction`) and the supply
# tx that would follow it (`originalTransaction`) -- we anchor the latter.
params = {
    "tool": "prepare_action",
    "action": "supply",
    "version": "v4",
    "sender": "0x00000000000000000000000000000000dEaDbEEF",
    "reserveId": "ODQ1Mzo6MHgxNzkwNURiMGU0QTM1MTQ0Njc1Mzk5NTZjMDg0MTgwNjE2QUU3QjhEOjo3",
    "amount": "0.005",
}
params_digest = sha256_hex(jcs(params))

# Confirmation — the real `data.originalTransaction` prepare_action
# returned: the unsigned supply call on the Base USDC v4 Spoke contract,
# exactly as the live server built it. Untouched, not reformatted beyond
# key order (JCS sorts keys; values are byte-identical to the response).
confirmation = {
    "to": "0x17905Db0e4A3514467539956c084180616AE7B8D",
    "from": "0x00000000000000000000000000000000DeaDBeef",
    "data": (
        "0x852a56a500000000000000000000000000000000000000000000000000000000000000"
        "0700000000000000000000000000000000000000000000000000000000000013880000"
        "00000000000000000000000000000000000000000000000000000000deadbeef"
    ),
    "value": "0",
    "chainId": 8453,
    "operations": ["SPOKE_SUPPLY"],
}
confirmation_digest = sha256_hex(jcs(confirmation))

# Result — MODELED, not live. get_transaction_processed's own tools/list
# entry declares no outputSchema, and its description names exactly one
# field: "processed" ("Poll until processed is true, then continue").
# Actually reaching this step would require signing the approval above,
# waiting for it to mine, signing the supply tx, and broadcasting it --
# spending real gas and moving real USDC through a wallet we would then
# have to fund, which is out of proportion to a worked example (same
# non-broadcast discipline wdk-action-ref-anchor and
# paypal-action-ref-anchor apply to their own result fields). No field
# beyond the one the server's own description names is invented.
result = {
    "processed": True,
}
result_digest = sha256_hex(jcs(result))

envelope = {
    "packet_version": "1.0",
    "action_ref": action_ref,
    "hash_algo": "sha256",
    "preimage_format": "jcs-rfc8785-v1",
    "preimage": preimage,
    "capability": "mcp.tool.prepare_action",
    "params_digest": params_digest,
    "confirmation_digest": confirmation_digest,
    "result_digest": result_digest,
    "generated_at_utc": timestamp,
}

manifest = {
    "fixture_id": "aave-mcp-prepare-action-supply-worked-example",
    "spec": "action-ref-v1 (argentum-core, docs/spec/action-ref.md)",
    "preimage": preimage,
    "jcs_payload": jcs_payload,
    "action_ref": action_ref,
    "anchor_ref_bytes32": "0x" + action_ref,
    "anchor_registry": "0x49fEcA52bC634a9Ab773226D16619deC547794aa",
    "anchor_chain": "Base mainnet (chainId 8453)",
    "envelope": envelope,
    "params": params,
    "confirmation": confirmation,
    "result": result,
    "provenance": (
        "params and confirmation are REAL: captured from a live tools/call "
        "request against Aave's official MCP server (mcp.aave.com) on "
        "2026-11-06T20:43:32.000Z, for a genuine Base mainnet (chainId 8453) "
        "USDC v4 market discovered via a real get_markets call in the same "
        "session. confirmation is prepare_action's own real "
        "data.originalTransaction -- the unsigned supply transaction the "
        "sender wallet would sign, byte-for-byte as the server returned it. "
        "The sender is the same obviously-synthetic 'dEaDbEEF' placeholder "
        "address wdk-action-ref-anchor uses, not a wallet we control; no "
        "approval was signed and no transaction was broadcast "
        "(prepare_action is declared readOnlyHint/destructiveHint:false by "
        "the server's own tools/list, so building it is free). result is "
        "MODELED, not live: get_transaction_processed's own tools/list "
        "entry declares no outputSchema and its description names exactly "
        "one field ('processed'); reaching that step for real would require "
        "signing and broadcasting both the approval and the supply "
        "transaction, spending real gas through a funded wallet, out of "
        "proportion to a worked example. No claim that mcp.aave.com or "
        "aave/skills emits action_ref today, and no claim of integration, "
        "adoption, or endorsement by Aave."
    ),
}

with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2, sort_keys=True)
    f.write("\n")

print("=== aave-action-ref-anchor : producer ===")
print(f"jcs_payload = {jcs_payload}")
print(f"action_ref  = {action_ref}")
print(f"anchor ref (bytes32) = 0x{action_ref}")
print(f"wrote {OUT_DIR}/manifest.json")
