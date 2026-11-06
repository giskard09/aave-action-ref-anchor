# Provenance — read this before drawing any conclusion

This document states exactly what is real and what is synthetic in this
worked example. Hard honesty is the point: the artifact is worthless if its
provenance is fuzzy.

## What is real

- `action_ref` is derived exactly per `action-ref-v1`
  ([argentum-core/docs/spec/action-ref.md](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)):
  SHA-256 of the RFC 8785 JCS canonicalization of the four preimage fields
  (`agent_id`, `action_type`, `scope`, `timestamp`).
- **`params` and `confirmation` are REAL — not modeled from source, captured
  live.** Unlike the companion worked examples for Tether's WDK
  (`wdk-action-ref-anchor`) and PayPal's agent-toolkit
  (`paypal-action-ref-anchor`), which model their envelope fields from the
  toolkits' own public npm source because no running server was available to
  call, Aave's MCP server is a live, public, hosted endpoint
  (`https://mcp.aave.com`) — the same one `aave/skills` points agents at. So
  this repo made real, documented, non-destructive calls against it instead
  of reading source:
  - `tools/list` against a real MCP session (initialized
    2026-11-06T20:40:57Z) confirmed `prepare_action`'s and
    `get_transaction_processed`'s actual declared `inputSchema`, and that
    the server marks `prepare_action` and `preview_action`
    `readOnlyHint: true, destructiveHint: false` — its own declaration that
    building an unsigned transaction sends nothing and costs nothing.
  - `get_markets({"symbols":["USDC"],"version":"v4"})` returned real,
    live Base mainnet (chainId 8453) market data, including the genuine
    opaque `reserveId`
    `ODQ1Mzo6MHgxNzkwNURiMGU0QTM1MTQ0Njc1Mzk5NTZjMDg0MTgwNjE2QUU3QjhEOjo3`
    used below.
  - `prepare_action({"action":"supply","version":"v4","sender":"0x00000000000000000000000000000000dEaDbEEF","reserveId":"...","amount":"0.005"})`,
    sent at request id 7 of that session (response `Date:` header
    `Fri, 06 Nov 2026 20:43:32 GMT`), returned a real
    `Erc20ApprovalRequired` envelope. `confirmation` in this repo's
    `artifacts/manifest.json` is that response's own
    `data.originalTransaction` field — the real, unsigned supply
    transaction (`to`, `data`, `value`, `chainId`, `operations`) the
    sender wallet would sign once the paired approval clears — copied
    byte-for-byte, not reformatted beyond JCS's key ordering. Repeating
    the identical request a minute later returned the same transaction
    with only the EIP-712 permit's `deadline` field changed (time-based),
    confirming this is a real deterministic server response, not a
    fabricated fixture.
- The on-chain anchor (once `artifacts/anchor.json` exists) is a real
  transaction on Base mainnet; the tx hash and block are independently
  checkable by anyone via `verifier/verify.py`.

## What is synthetic — declared

- **The sender address is a placeholder, not a wallet we control.**
  `0x00000000000000000000000000000000dEaDbEEF` is the same
  obviously-fake "dEaDbEEF" convention `wdk-action-ref-anchor` uses. It is
  a well-known public burn address that other people's dust ends up at —
  it happened to hold exactly 0.01 USDC on Base at call time, which is why
  the modeled amount (`0.005`) is sized under that rather than at a
  rounder number: `prepare_action` checks the sender's real balance even
  to build an unsigned transaction (an attempt at `500` was rejected live
  with `INSUFFICIENT_BALANCE: Sender holds 0.010000 USDC`), so a larger
  amount would not have produced a buildable transaction to anchor. No
  approval was ever signed and no transaction was ever broadcast —
  `prepare_action` itself never sends anything, per the server's own
  `readOnlyHint`/`destructiveHint` declaration, so making this call cost
  nothing and touched no funds beyond the dust already sitting at that
  address before we ever queried it.
- **`result` is MODELED, not live.** `get_transaction_processed`'s own
  `tools/list` entry declares no `outputSchema`, and its description names
  exactly one field: `"processed"` ("Poll until processed is true, then
  continue"). `artifacts/manifest.json`'s `result` is `{"processed": true}`
  — nothing beyond that one named field is invented. Reaching this step for
  real would require signing the pending approval, waiting for it to mine,
  signing the resulting supply transaction, and broadcasting it — spending
  real gas and moving real USDC through a wallet we would first have to
  fund — out of proportion to a worked example, the same non-broadcast
  discipline `wdk-action-ref-anchor` and `paypal-action-ref-anchor` apply to
  their own `result` fields.

## What this therefore does and does not show

- **Does show:** the `action_ref` derivation applies unchanged to a real,
  live tool call against Aave's own production MCP server — not a
  hypothetical shape read from source, but the actual
  `data.originalTransaction` a real agent session would hand a real user to
  sign. It also surfaces the same structural gap `wdk-action-ref-anchor`
  does, now admitted in Aave's own words: `tx-confirmation/SKILL.md` states
  plainly that "Aave's feed reads current state and history; it does not
  carry a receipt, block or gas figure. Where the user wants those, say
  they come from a block explorer, not from here." `get_transaction_processed`'s
  only declared output field, `processed`, is a boolean read from that same
  feed — pre-execution approval (the unsigned transaction) is real and
  anchorable; post-execution accountability, by the server's own
  documentation, is a status flag with no receipt, block, or gas figure
  attached, and nothing independent of Aave's own indexer to check it
  against.
- **Does not show:** that `mcp.aave.com` or `aave/skills` emits
  `action_ref` today, or that it will. It is our worked example applying a
  public spec to Aave's real, live, public MCP server. No claim of
  integration, endorsement, or adoption by Aave, and no claim that the
  signed, broadcast version of this transaction ever existed — only the
  unsigned one the server actually returned.
