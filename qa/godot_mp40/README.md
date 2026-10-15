# Native Godot 4.6 renderer probe – existing game art model

A **real Godot renderer** CI check against the publicly licensed Moony_State MP40 GLB. Pulls the pinned 4.4MB source from Zenodo, checks MD5, imports it as glTF in Godot **4.6**, renders background, hip, centered view and alternate pose, then rejects missing, black and near-identical screenshots.

**Important:** This tests **the original CC BY 4.0 model and texture**, NOT the 19MB locally generated V8 PBR asset (which is not in this repository), nor the original Godot church scene, nor gameplay/animation, nor Android. The file is stored in CI only and the original license/attribution must be retained. The test cannot claim success until its GitHub Actions job completes and image gate passes.

Model source: https://sketchfab.com/3d-models/mp-40-ww2-submachine-gun-7ec7e1f9656e4319b8edae0d785699ad

Render images and machine-readable proof are kept in the workflow artifacts even if the gate reports RED. No new engine/project or replacement church map is introduced.