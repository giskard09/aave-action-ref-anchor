# aave-action-ref-anchor

A worked example that derives an **`action_ref`** — a deterministic,
content-addressed identifier for an agent action
([`action-ref-v1`](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)) —
for a real **`prepare_action`** (supply) tool call against
[Aave's official MCP server](https://mcp.aave.com) (the server
[`aave/skills`](https://github.com/aave/skills)' MCP plugin points agents
at), and anchors it permissionlessly on-chain, giving it a property the
tool call does not have on its own: an **externally verifiable,
third-party-checkable record of what unsigned transaction was prepared**,
independent of Aave's own feed or any host application's logs.

The timestamp of the anchor is the point. This is not outreach and not a
claim of adoption — it is a worked example, byte-exact against the public
spec and, this time, against a **real live call** to Aave's production MCP
server, not source read offline.

> **Provenance, up front (read `PROVENANCE.md` for the full statement).**
> `params` and `confirmation` in this repo are **real** — captured from an
> actual `tools/call` request against `mcp.aave.com` on
> 2026-11-06T20:43:32.000Z, for a genuine Base mainnet USDC v4 market. No
> approval was signed and no transaction was broadcast (`prepare_action`
> itself never sends anything). The sender address is an obviously-synthetic
> placeholder, not a wallet we control. `result` is modeled, not live — see
> `PROVENANCE.md` for exactly why. Nothing here — on-chain or in this repo
> — implies that Aave integrated, endorsed, or participated.

## The gap, in Aave's own words

[`plugins/mcp/skills/safe-transactions/SKILL.md`](https://github.com/aave/skills/blob/main/plugins/mcp/skills/safe-transactions/SKILL.md)
documents the chain `prepare_action` sits in: *"every tool here returns an
**unsigned** transaction for the user's own wallet to sign … then stop:
signing is the user's move."* That pre-execution approval step is real and,
as this repo shows, anchorable exactly as returned.

[`plugins/mcp/skills/tx-confirmation/SKILL.md`](https://github.com/aave/skills/blob/main/plugins/mcp/skills/tx-confirmation/SKILL.md)
documents what happens after: *"A transaction hash is not a result … Aave's
feed reads current state and history; it does not carry a receipt, block or
gas figure. Where the user wants those, say they come from a block
explorer, not from here."* `get_transaction_processed` — the tool
`AGENTS.md` says to poll before building a dependent step — declares no
output schema and names exactly one field in its own description:
`processed`, a boolean. That is the same shape as `wdk-action-ref-anchor`'s
gap: pre-execution approval has real structure to anchor; post-execution
accountability, by the server's own documentation, does not.

## The idea

`prepare_action`'s real response (`data.originalTransaction`, captured live
— see `PROVENANCE.md`) is the unsigned transaction a real agent session
would hand a real user to sign: `to`, `data`, `value`, `chainId`, and the
`operations` array `get_transaction_processed` requires to later poll for
confirmation. `action_ref` gives that moment a content-addressed identifier
any party can recompute from four declared fields (`agent_id`,
`action_type`, `scope`, `timestamp`) — no trust in the emitting system
required. This repo extends that with an **envelope** carrying
`params_digest` (the declared tool input), `confirmation_digest` (the real
unsigned transaction), and `result_digest` (the one field
`get_transaction_processed` actually names) — hashes of the exact context a
verifier would need to confirm what was requested and what was prepared,
independently recomputable from the declared JSON.

```
   mcp.aave.com `prepare_action` call        public chain (Base)
   ┌───────────────────────────┐            ┌────────────────────────┐
   │ agent_id, action_type,     │  JCS+SHA256│ AnchorRegistry         │
   │ scope, timestamp           │───────────▶│  anchor(bytes32 ref)   │
   │ + params/confirmation/     │  action_ref│  Anchored(ref,by,time) │
   │   result digests (envelope)│            └────────────────────────┘
   └───────────────────────────┘             operator-independent
        no external record                   timestamp / finality
```

## Doctrine: spec-agnostic to Aave's format

We derive `action_ref` from the four canonical fields only. We do **not**
ask `aave/skills` or `mcp.aave.com` to adopt any anchoring infrastructure,
change their tool schemas, or emit any new fields. The integration lives
entirely in how a `prepare_action` call *could* be shaped and anchored; the
server's real, live response is the input, the anchor is the added
property.

## What's here

| Path | What it is |
|------|-----------|
| `scripts/produce.py` | Derives `action_ref` per `action-ref-v1` (JCS RFC 8785 + SHA-256) for a real `prepare_action` (supply) call against `mcp.aave.com`, plus the `params_digest`/`confirmation_digest`/`result_digest` envelope. |
| `verifier/verify.py` | Independent (stdlib-only) verifier: recomputes all three digests from the declared JSON and confirms the matching `Anchored` event on Base mainnet. |
| `artifacts/` | The canonical instance: `manifest.json` (preimage, digests, envelope) and `anchor.json` (tx/block, once anchored). |
| `scripts/anchor.sh` | The exact `cast` command used to anchor `action_ref`. |
| `PROVENANCE.md` | Exactly what is and isn't real about this artifact. Read it. |

## Reproduce

```bash
# 1. derive action_ref + the envelope digests (re-querying mcp.aave.com is
#    optional -- the real response is already embedded in the script)
python3 scripts/produce.py artifacts

# 2. anchor action_ref on Base mainnet (see scripts/anchor.sh)

# 3. independently verify the derivation and the on-chain anchor
python3 verifier/verify.py
```

## The anchor

- **Registry:** `0x49fEcA52bC634a9Ab773226D16619deC547794aa` (same CREATE2
  address on Base 8453, Arbitrum One 42161, Ink 57073).
- **Function:** `anchor(bytes32 ref)` — permissionless, no owner/roles/funds.
- **Event:** `Anchored(bytes32 indexed ref, address indexed anchoredBy, uint256 timestamp)`.
- The anchored `ref` for this instance and its tx/block are in
  `artifacts/anchor.json`.

## Related worked examples

Same pattern, other formats: [`dapr-history-anchor`](https://github.com/giskard09/dapr-history-anchor)
(Dapr Verifiable Execution), [`scitt-capsule-anchor`](https://github.com/giskard09/scitt-capsule-anchor)
(SCITT Agent Action Capsule), [`r0x-action-ref-anchor`](https://github.com/giskard09/r0x-action-ref-anchor)
(Robinhood Chain / project-r0x), [`pay-kit-action-ref-anchor`](https://github.com/giskard09/pay-kit-action-ref-anchor)
(Solana Foundation pay-kit MPP), [`wdk-action-ref-anchor`](https://github.com/giskard09/wdk-action-ref-anchor)
(Tether Wallet Development Kit MCP toolkit), [`paypal-action-ref-anchor`](https://github.com/giskard09/paypal-action-ref-anchor)
(PayPal agent-toolkit).

## License

MIT.
