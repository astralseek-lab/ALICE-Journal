# ALICE Journal

ALICE-Journal is the public repository of the ALICE network at AstralSeek Lab.

## What's inside each package

- `paper_text.txt` — the distilled study text (required input for reproduction);
- `SHA256SUMS.txt` — the per-file hash ledger of the package;
- `pkg-A/`, `pkg-B/` — two independent implementation lines, each with code,
  the evidence chain (`evidence/`, `deviations/`, `evidence.graph.json`),
  and its task brief;
- top-level ontology / data files (e.g. `*.owl`, `*.xlsx`, `*.csv`) — input copies.

## How to use

Pick the folder you need, copy its link, and paste it to ALICE
(<https://astralseek.bio/>) — then start your research.

## Directory tree (grouped by research area)

1. **Behaviour Change Technique Ontologies (BCIO / BCTO family)** — the
   conceptual engineering behind behaviour-change interventions: from the BCT
   ontology and taxonomy, through the BCIO modules (Mechanisms of Action,
   Mode of Delivery, Behaviour, Upper Level, Setting, Source, Style, Schedule,
   Population), to methodology and data-extraction templates.
   New research areas will be added below as sibling groups; follow the tree
   straight into each task-package folder.

- [ALICE-2026-0001](ALICE-2026-0001/) — Marques 2024 · BCT ontology build (`bcto.owl`)
- [ALICE-2026-0002](ALICE-2026-0002/) — Schenk 2023 · Mechanisms of Action ontology (`bcio_moa.owl`)
- [ALICE-2026-0003](ALICE-2026-0003/) — Marques 2020 · Mode of Delivery ontology (`bcio_mode_of_delivery.owl`, with Upper Level)
- [ALICE-2026-0004](ALICE-2026-0004/) — Schenk 2024 · Behaviour / Style / Upper Level ontology views
- [ALICE-2026-0005](ALICE-2026-0005/) — Michie 2020 · Upper Level ontology (`bcio_upper_level.owl`, with Style)
- [ALICE-2026-0006](ALICE-2026-0006/) — Norris 2020 · Setting ontology (`bcio_setting.owl`)
- [ALICE-2026-0007](ALICE-2026-0007/) — Norris 2021 · Source ontology (`bcio_source.owl`)
- [ALICE-2026-0008](ALICE-2026-0008/) — Wright 2023 · Style ontology (`bcio_style.owl`, with Behaviour / Upper Level)
- [ALICE-2026-0009](ALICE-2026-0009/) — Marques 2024 · Schedule ontology (`bcio_schedule.owl`, with Mode of Delivery / Upper Level)
- [ALICE-2026-0010](ALICE-2026-0010/) — Wright 2025 · Population ontology (`bcio_population.owl`, with Style)
- [ALICE-2026-0011](ALICE-2026-0011/) — Wright 2020 · methods unit (step counting, no ontology file)
- [ALICE-2026-0012](ALICE-2026-0012/) — Norris 2024 · data-extraction template (xlsx / csv)
- [ALICE-2026-0013](ALICE-2026-0013/) — Zhang 2025 · terminology mapping table (csv)
- [ALICE-2026-0014](ALICE-2026-0014/) — Michie 2013 · BCT Taxonomy v1 terminology table (`terms_bct_v1.csv`)
