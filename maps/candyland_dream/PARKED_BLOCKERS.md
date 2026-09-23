# Candyland Dream — Parked Blockers & Brainstorm Later

Updated: 2026-09-23

Purpose: keep stalled or low-value-blocking work documented without letting it slow the main Candyland build.

## What is already working

The following pieces are **not blocked**:

- CandyAssetScanner v0.7 passes end-to-end.
- Scanner contract tests pass.
- GroundingDINO detection works on the Candyland renders.
- Segmentation/crops are generated.
- Proxy GLBs are generated.
- Blender scanner gallery import/render works.
- World build + hero renders pass.
- Cinematic preview pass works.
- Original audio + open-pack manifest pass works.
- Independent GLB validation passes.
- NZ:P/Vril compiler compatibility passes.

Latest fully successful scanner run:
- Workflow: CandyAssetScanner v0.7
- Run: 35854129981
- Result: SUCCESS

Latest production run:
- Workflow: Candyland Dream Seven-Agent Production Pipeline
- Run: 35854126851
- Overall result: FAILURE because Agent 2 failed; most other jobs passed.

---

## PARKED BLOCKER 1 — Asset catalog hard cap

### Status
FIX IMPLEMENTED — VALIDATION RUNNING

### Exact failure
Agent 2 — Open-license asset scout + catalog failed while rendering the individual asset catalog.

Blender error:

```
RuntimeError: Expected 30-240 visible ENV/PROPS meshes, got 260
```

Because the catalog renderer aborted before creating its manifest, the workflow then also hit:

```
FileNotFoundError: candyland/catalog/catalog_manifest.json
```

### Why this matters
- World build itself passed.
- Cinematic passed.
- GLB validation passed.
- Compiler passed.
- But Agent 2 failure caused Agent 7 Android final gate to be skipped.

### Root cause
The world now contains more visible catalog-eligible ENV/PROPS meshes than the catalog script's old maximum allows.

Current visible count:
- 260

Current allowed maximum:
- 240

### Brainstorm later
Possible solutions:

1. Raise the catalog maximum safely.
2. Split the catalog into pages/batches.
3. Mark repeated/decorative meshes with `catalog_skip=True`.
4. Group repeated assets into families instead of cataloging every instance.
5. Catalog only unique source assets rather than every placed mesh.
6. Add a dedupe stage before catalog rendering.
7. Create separate ENV and PROPS catalogs.

### Implemented direction
The catalog now follows the long-term design instead of raising the cap:
- unique asset-family catalog
- numbered/repeated placements deduplicated
- instance membership/counts preserved in the manifest
- paginated contact sheets
- only a high sanity ceiling remains for pathological scenes

Implementation commits:
- `6816c6303383e57d5538148d4467ee038f8e17dc`
- `38e16097b0fa632b920a24bc70109f3d9e3222b0`

Validation run: `35856563047`

---

## PARKED BLOCKER 2 — High-quality neural 3D replacements

### Status
PIPELINE READY, HIGH-QUALITY BACKEND NOT YET EXECUTING IN CURRENT CI

### What works
CandyAssetScanner currently produces:
- detections
- masks
- RGBA crops
- stable item IDs
- proxy GLBs
- quality queue
- Blender import
- QA gallery

The scanner detected and queued 27 Candyland items in the successful v0.7 pass.

### What is missing
The proxy meshes have not yet been automatically replaced by confirmed production-quality neural 3D outputs.

Prepared backends:
- TRELLIS — preferred quality path
- TripoSR — fast path
- Hunyuan3D — optional texture/PBR path after exact model/license verification

### Why it is parked
The current GitHub CPU runner is good for detection and proxy generation, but high-quality reconstruction is a GPU-heavy workload and should not be forced into the normal CPU CI path without an appropriate GPU runner/service.

### Brainstorm later
Options:

1. GitHub self-hosted NVIDIA runner.
2. Hugging Face GPU Space/endpoint.
3. RunPod/Vast/other GPU worker.
4. Local Windows/NVIDIA machine worker.
5. Dedicated reconstruction service with a queue.
6. Use TripoSR for cheap first-pass assets and TRELLIS only for hero props.
7. Generate multi-view references first, then reconstruct.

### Recommended future direction
Use a separate GPU queue rather than making every normal map build depend on neural reconstruction.

---

## PARKED BLOCKER 3 — GitHub Copilot cloud-agent assignment

### Status
BLOCKED BY GITHUB PERMISSION / POLICY

### Attempt
Issues #2 and #5 were prepared for coding-agent work.

Tried assigning:

```
copilot-swe-agent[bot]
```

GitHub returned:

```
403 Forbidden
```

for both assignments.

### What this means
The repository/account policy currently does not permit assigning the Copilot SWE cloud agent through the available GitHub connection.

### Impact
Low.

The project still has:
- GitHub Actions automation
- four documented agent roles
- scanner automation
- build automation
- testing
- research/data scout instructions
- coding support/QA instructions

### Brainstorm later
- Enable/configure Copilot coding agent for the repository/account.
- Check repository agent policy/permissions.
- Use an OpenAI/Codex agent runtime connected to GitHub.
- Keep GitHub Actions as the deterministic execution layer and use agents only for code changes.

---

## Current four-agent state

### Agent A — Build Engineer
Active capability:
- world build
- Blender automation
- hero renders
- GLB export
- compiler integration

Current dependency:
- final production gate is indirectly blocked by Agent 2 catalog failure.

### Agent B — 3D Asset Engineer
Active capability:
- detection
- segmentation
- proxy reconstruction
- stable asset IDs
- Blender QA

Parked upgrade:
- production-quality neural GLB generation needs a GPU execution path.

### Agent C — Research/Data Scout
Active:
- tool/license research
- source manifest
- fallback discovery

Current recorded candidates include:
- InstantMesh
- Instant Meshes
- pyinstantmeshes
- Open3D

### Agent D — Coding Support & QA
Active:
- scanner contract tests
- CI/API compatibility fixes
- workflow diagnostics

Latest scanner CI with Agent D tests:
- SUCCESS

---

## Resume order when we brainstorm again

1. Fix catalog architecture instead of only increasing the mesh limit.
2. Re-run production pipeline and unlock Agent 7 final gate.
3. Decide GPU execution provider for neural 3D.
4. Run high-quality reconstruction on the top 10 hero assets.
5. Compare proxy vs neural assets in Blender.
6. Integrate only assets that visibly improve the map.
7. Revisit optional Copilot cloud-agent permissions last.

## Guiding rule

Do not let experimental agent/GPU tooling block the playable map.

The map build, scanner, compiler, and validated artifacts remain the priority.
