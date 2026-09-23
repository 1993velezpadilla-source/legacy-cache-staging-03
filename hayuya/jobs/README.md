# HAYUYA requests for Felix / Volnox

This repository is Felix/Volnox's independent workspace.

To request a HAYUYA model, an authorized agent should:

1. store the reference images in this repository;
2. create one immutable request file under:
   `hayuya/jobs/requests/<job_id>.json`
3. use a globally unique job id such as:
   `felix-hospital-monster-001`

The central HAYUYA bridge periodically picks up these requests and runs them using the main HAYUYA GPU pool.

Felix does not need to edit the main HAYUYA repository.

Request example:

```json
{
  "schema": 1,
  "job_id": "felix-hospital-monster-001",
  "owner": "Felix",
  "title": "Hospital monster",
  "geometry_input": "hayuya/assets/hospital-monster/front.png",
  "reference_dir": "hayuya/assets/hospital-monster/references",
  "detail_dir": "hayuya/assets/hospital-monster/details",
  "profile": "monster",
  "mode": "character",
  "portable_target": "auto",
  "gpu_vram": 24,
  "backends": "triposg,trellis2,trellis,instantmesh,triposr"
}
```

Do not overwrite an old request to revise a model. Create a new job id.
