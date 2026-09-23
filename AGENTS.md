# Candyland Dream Agent Operating Guide

This repository uses two primary autonomous roles for Candyland work. Both roles must read:
- FELIX_ENTRY.md
- TOOLBOX_POLICY.md
- WORK_RULES.md
- HAYUYA_3D_WORKFLOW.md
- CROSS_REPO_REFERENCE.md
- GITHUB_HANDSHAKE.md
- research/CANDYLAND_7_AGENT_OPEN_TOOLING.md
- maps/candyland_dream/scanner/README.md

## Agent A — Candyland Build Engineer
Instruction file: .agents/candyland-build-engineer.md

Owns repository changes, tests, workflows, Blender automation code, GLB validation, engine compile, Android QA, bug repair, and integration.

## Agent B — Candyland 3D Asset Engineer
Instruction file: .agents/candyland-3d-asset-engineer.md

Owns reference scanning, object detection/segmentation, 3D reconstruction queues, mesh cleanup, material transfer, asset catalog QA, and replacement of low-quality proxies.

## Shared rule
Never accept a visual claim without a rendered artifact. Never accept a build claim without a machine-readable report or CI result. Preserve license provenance for every external model, texture, sound, and tool.


## Agent C — Candyland Research & Data Scout
Instruction file: .agents/candyland-research-scout.md

Owns source discovery, license verification, data/tool research, and fallback identification.

## Agent D — Candyland Coding Support & QA
Instruction file: .agents/candyland-code-support.md

Owns debugging support, code review, tests, workflow reliability, and failure repair.
