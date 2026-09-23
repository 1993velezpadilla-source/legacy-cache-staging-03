# Candyland Blocker Research — 2026-09-23

This note records web research and implementation decisions for the stalled Candyland tasks.

## 1. Scalable Blender asset catalog

### Problem
The production pipeline failed because the catalog script had a hard maximum of 240 visible ENV/PROPS meshes while the v0.7 world had 260.

### Research-backed design decision
Treat the catalog as an **asset-family catalog**, not a placed-object inventory.

Production fix implemented:
- remove the brittle 240-object ceiling;
- keep only a high absolute sanity guard;
- group repeated numbered instances into stable families;
- preserve instance membership/counts in the manifest;
- render one representative per family;
- paginate contact sheets.

This prevents richer maps from breaking CI simply because more copies of valid props are placed.

### Current implementation
- `maps/candyland_dream/blender/render_candyland_catalog_v04.py`
- workflow validates family count against source-object count;
- contact sheets are paginated at 60 families/page.

## 2. GPU lane for high-quality 3D reconstruction

### Official requirements found
TRELLIS official repository:
- Linux tested;
- NVIDIA GPU with at least 16 GB VRAM;
- validated on A100/A6000;
- CUDA toolkit required for some compiled submodules.

Hunyuan3D-2.1 official repository:
- shape generation: about 10 GB VRAM;
- texture generation: about 21 GB VRAM;
- combined shape + texture: about 29 GB VRAM.

### GitHub runner finding
GitHub managed GPU larger runner:
- Tesla T4;
- 16 GB VRAM;
- larger runners require organization/enterprise GitHub plans.

This repository is currently owned by a personal GitHub user, so GitHub managed GPU larger runners are not a dependable option for the current repo ownership.

### Hugging Face finding
Current GPU Spaces/Endpoints include:
- T4: 16 GB;
- L4/A10G: 24 GB;
- L40S: 48 GB;
- A100: 80 GB.

ZeroGPU offers 48 GB and 96 GB allocations, but it is Gradio-specific and has compatibility constraints.

### Decision
Preferred dependable production lane:
1. keep normal GitHub Actions CPU workflows for detection, segmentation, proxy GLBs, Blender build, engine and Android QA;
2. use a separate GPU reconstruction worker;
3. target **L40S 48 GB** or **A100 80 GB** for hero-asset reconstruction;
4. keep TRELLIS as preferred geometry backend;
5. keep TripoSR as fast fallback;
6. run Hunyuan3D texture/PBR only on selected hero assets;
7. return GLBs under the same stable scanner item IDs.

This isolates expensive/fragile GPU dependencies from the deterministic map build.

## 3. Copilot cloud-agent assignment

### Official GitHub finding
For personal repositories, Copilot cloud agent is available on paid Copilot plans and is enabled by default unless repository access was disabled.

GitHub's documented path:
- Profile picture
- Copilot settings
- Cloud agent
- Repository access
- choose All repositories or include the target repository

GitHub troubleshooting also states that if Copilot does not appear as an assignee, confirm a paid Copilot plan and that cloud agent has not been disabled for the repository.

### Current repo/API observation
Direct bot assignment through the connected GitHub integration returned HTTP 403.

### Interpretation
The remaining causes to check are:
- personal GitHub account does not have an eligible paid Copilot plan;
- Cloud agent repository access is disabled;
- the connected GitHub integration lacks the permission needed to assign the Copilot agent even when the account itself can do so in the GitHub UI.

### Decision
Do not block Candyland on this.
Continue GitHub Actions + four-agent repo instructions as the deterministic execution layer. Revisit Copilot assignment only after the account policy is confirmed.

## 4. Strong automation architecture

### Deterministic lane
GitHub Actions:
- scanner contract tests
- semantic detection
- segmentation
- proxy GLB generation
- Blender map build
- deduplicated catalog
- cinematic
- GLB validation
- engine compile
- Android runtime gate

### GPU lane
External worker:
- consume `quality_queue.json`;
- reconstruct top-ranked items;
- preserve stable item ID;
- validate nonzero GLB;
- run mesh cleanup/retopology;
- render isolated QA;
- return approved GLBs + manifest.

### Support lane
Agent C:
- current source/license/model research.

Agent D:
- tests, workflow/API drift repair, artifact validation.

## Official sources

- GitHub larger runners: https://docs.github.com/en/actions/concepts/runners/larger-runners
- GitHub larger runner specs: https://docs.github.com/en/actions/reference/runners/larger-runners
- GitHub Copilot personal policies: https://docs.github.com/en/copilot/how-tos/manage-your-account/manage-policies
- GitHub Copilot cloud-agent troubleshooting: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/troubleshoot-cloud-agent
- TRELLIS: https://github.com/microsoft/TRELLIS
- Hunyuan3D-2.1: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- Hugging Face GPU Spaces: https://huggingface.co/docs/hub/spaces-gpus
- Hugging Face ZeroGPU: https://huggingface.co/docs/hub/spaces-zerogpu
- Hugging Face Inference Endpoints: https://huggingface.co/docs/inference-endpoints/guides/configuration

## Current status

- Catalog blocker: **FIX IMPLEMENTED, CI VALIDATION RUNNING**
- GPU reconstruction: **ARCHITECTURE DECIDED; provider/credential connection still required**
- Copilot assignment: **documented; non-blocking**
