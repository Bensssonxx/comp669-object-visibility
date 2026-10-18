# Current state

Updated 2026-10-18, America/New_York.

Active objective: implement the revised object-visibility-aware AIMv2/DINOv2 project, execute a real pilot, and prepare reviewable milestone evidence. Canvas remains read-only; do not submit work or send messages to the instructor without user authorization.

Completed: isolated project environment; official model code/checkpoints pinned; both encoders pass actual MPS inference benchmarks; complete Pet mirror verified against official filenames/labels/splits, plus 100 original JPEG byte comparisons; protocol written before dataset predictions; 14 empty-foreground annotation exclusions recorded before sampling; 24 mask/data safety tests pass.

Pilot v1: 1,480 train / 370 validation / 185 test images, 37 breeds. AIMv2 then DINOv2 run sequentially. Read `results/pilot_v1/*-run.log` and actual prediction files before claiming completion. No classifier or dataset metrics should be inferred from model benchmark success.

Next: complete both inference runs, analyze paired predictions, visually inspect figures, write bilingual evidence report, verify repository tracking excludes data/weights/private Canvas material, and create the GitHub destination if an authorized signed-in route is available. CLI GitHub is not signed in; the connected GitHub account is Bensssonxx. Private remote repository created and verified: https://github.com/Bensssonxx/comp669-object-visibility. Existing HTTPS Git credential helper works.

Milestone: Part 2 slides due Oct 21, 2026 at 11:59 PM ET; presentation Oct 22, 12 minutes plus 1–2 minutes Q&A. Must include preliminary results, analysis, additional experiments, repository link and AI-use disclosure. These dates were checked live in this chat on Oct 18.
