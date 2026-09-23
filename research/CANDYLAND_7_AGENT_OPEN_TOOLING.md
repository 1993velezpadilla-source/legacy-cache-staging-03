# Candyland Dream — Seven-Agent Open Tooling & Asset Matrix

Reviewed: 2026-09-23
Purpose: shared source policy for the seven-agent Candyland production pipeline.

## License gate

Production preference:
1. CC0 / public domain for redistributable models, textures, audio and footage.
2. MIT / BSD / Apache for reusable tooling.
3. CC-BY may be used only when attribution is preserved in provenance and release credits.
4. Custom, NC, unclear, or conflicting licenses are reference-only until reviewed and recorded.
5. Every imported external asset must record source URL, license, version/commit where possible, and local SHA-256.

## AI / LLM assistance candidates

### harveyxiacn/blender-mcp
- Use: bridge an MCP-capable AI assistant to a live Blender session.
- License: MIT.
- Status: APPROVED TOOLING CANDIDATE.
- Runtime note: requires Blender to be installed/running on the machine that exposes the MCP server.
- Source: https://github.com/harveyxiacn/blender-mcp

### Aider-AI/aider
- Use: repo-aware coding assistant capable of working with local or hosted LLMs.
- License: Apache-2.0.
- Status: APPROVED TOOLING CANDIDATE.
- Source: https://github.com/Aider-AI/aider

### openai/shap-e
- Use: text/image-conditioned 3D generation experiments.
- Repository license: MIT.
- Status: APPROVED EXPERIMENTAL TOOLING; generated outputs still require visual/runtime QA.
- Source: https://github.com/openai/shap-e

### microsoft/TRELLIS
- Use: image-to-3D asset experiments and GLB extraction.
- License note: models and majority of code are MIT, but documented submodules/dependencies can have different licenses.
- Status: CONDITIONAL; dependency/license audit required for the exact runtime bundle before redistribution.
- Source: https://github.com/microsoft/TRELLIS

## Redistributable 3D / texture sources

### Poly Haven
- Assets: HDRIs, textures, 3D models.
- License: CC0.
- Status: APPROVED.
- Source: https://polyhaven.com/license

### Kenney
- Assets: 2D/3D game assets and audio packs.
- Asset pages identify game assets as CC0.
- High-value Candyland candidates:
  - Food Kit (3D)
  - Nature Kit (3D)
  - Building Kit / Fantasy Town Kit (3D)
  - Impact Sounds
  - Interface Sounds
  - UI Audio
- Status: APPROVED when the downloaded pack includes/retains its CC0 license.
- Source: https://kenney.nl/support

### SkywolfGameStudios/CC0Tree
- Assets: lightweight low-poly FBX environmental props.
- License: CC0-1.0.
- Status: APPROVED; already used by the Candyland audit.
- Source: https://github.com/SkywolfGameStudios/CC0Tree

### KayKit-Game-Assets/KayKit-Restaurant-Bits-1.0
- Assets: low-poly restaurant/food props in common 3D formats.
- License: CC0.
- Status: APPROVED CANDIDATE for giant-food scenery and dressing.
- Source: https://github.com/KayKit-Game-Assets/KayKit-Restaurant-Bits-1.0

## Audio

### Kenney audio packs
- Impact Sounds: CC0.
- Interface Sounds: CC0.
- UI Audio: CC0.
- Status: APPROVED.

### Freesound
- Per-file licenses vary.
- Only CC0 files are automatically eligible for the no-attribution production pool.
- CC-BY files require attribution tracking.
- CC-BY-NC is excluded from commercial-ready production.
- Status: FILTERED SOURCE, not blanket-approved.
- Source: https://freesound.org/help/faq/

## Video / cinematic source policy

The preferred production path is to render original Candyland footage from the Blender scene. This avoids stock-footage license drift and keeps visual continuity.

Blender demo/open-movie resources can be used for technique/reference where the specific item is CC-BY or CC-BY-SA and attribution is preserved. Do not assume every Blender-hosted demo file has the same license; record the license shown for the exact download.

## Quaternius caution

Current Quaternius pages show mixed/changed licensing information across pages and dates. Do not ingest a Quaternius pack automatically unless the exact downloaded pack's license/version is captured. Treat it as reference-only by default.

## Seven-agent handoff rule

Each agent must:
- consume upstream artifacts instead of recreating them;
- write a machine-readable report;
- record external provenance;
- fail loudly when required files are missing;
- never silently replace a licensed asset with an untracked download;
- use generated/original fallback content when an external pack cannot be safely acquired.
