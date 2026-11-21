# Five Friends Horde 48–54 — changelog

## v0.3.1-rc4 (November 21, 2026)

- Repaired navigation-stage structure: 13 multi-location steps split into a total of 34 geographically coherent steps, giving **320** stages in 13 chapters; quest goal order preserved.
- Added source-verified NPC coordinates for Eitrigg (quest 95283), Ekkal (86746) and Belgrom (91531), plus a search-area coordinate for Legashi objectives.
- Replaced the false "courier" treatment of More Valuable Than Gold (96337) with the Moonbrook inn's loose-floorboards Document Box work stage. Un'Goro's It's a Secret to Everybody (3845) now tracks its three separate inventory objectives instead of going straight to Linken.
- Left existing multi-stop Shen'dralas/Un'Goro pylon circuits, Jintha'Alor and Searing Gorge travel waypoints in order and untouched where a split would cause backtracking.
- Ensured **170 unique turn-ins**, 170 quest accepts, all goal phases chronological, and no manual task gate. Static build/routing check and Lua 5.4 registration stubs pass.
- Bundled a reproducible source build (old source required non-existent temporary paths), offline tests, current route JSON, source references, route PDF, and GitHub release workflow.
- Kept intentionally unknown dungeon interior coordinates unknown: no fabricated `Legs.lua` or indoor route polygon. Core Polestar/Nav and live-client tests remain requirements.

## v0.3.0-rc3 (November 21, 2026)

- First quest-aware goal compilation based on the revised 48–54 plan: 13 linked chapters, 297 steps, 170 accept/turn-in goals, 97 complete goals, 51 kill goals, and 37 authored goto nodes.
- Restored missing objectives and source-derived location hints; fixed garden/Temple/Maraudon and WPL prerequisite ordering; declared core Polestar nav dependency.
- Static QA and Lua 5.4 registration stubs only; original authoring rebuild source omitted prior guide/reference inputs.
