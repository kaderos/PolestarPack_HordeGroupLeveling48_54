# Reproducible source rebuild

This source package contains everything needed to regenerate the shipped format-5 compiled guide and addon. Unlike 0.3.0-rc3 it requires no external `/mnt/data/polestar_fix` or `/mnt/data/polestar_build` filesystem trees.

## Inputs checked into the source package

- `evidence/route-ledger.json`: revised researched quest/order/XP model (13 chapters, 170 quests).
- `inputs/prev/guides/*.guide`: the relevant original 43–48 guide sources from `Five_Friends_Polestar_GitHub_Repo_v1.2.1.zip`.
- `inputs/prev/addon/PolestarPack_FiveFriends4348/MapFrames.lua`: compatible map frame registration from that historical pack.
- `inputs/ref49/build/compiled-payloads.json`: the old 49–54 source's compiled guide cache (reference to preserve specific route stops, not shipped as another addon).
- `inputs/ref49/reference/{quests,npcs,items}.json`: historical focused Forever quest/objective and spawn cache with provenance `inputs/ref49/reference/PROVENANCE.json`.
- `docs/LOCATION_EVIDENCE.md`: provenance of the newly verified rc4 NPC and quest objective locations.

## Rebuild

Use Python 3.10+, and on Linux install `liblua5.4-0` to run the Lua registration smoke test:

```bash
python3 scripts/rebuild.py
```

The runner executes, in order, `build_navigation.py` (reconstruct baseline quest goals from the historical sources), `enrich_navigation.py` (rc4 geographical splits and missing objective stages), `validate_navigation.py`, `validate_regressions.py`, and `validate_lua.py` (actual Lua 5.4 parser with a Polestar API registration stub). The rebuilt guide data is in `build/compiled-guides.json` and the runtime addon is in `addon/PolestarPack_FiveFriends4854/`.

On machines without Lua 5.4, `python3 scripts/rebuild.py --skip-lua` performs the Python tests but explicitly skips Lua execution. The CI workflow installs Lua and runs all checks.

Run `python3 scripts/package_release.py` to create the ZIPs and SHA256SUMS in the repository parent (or supply `--out <path>`). The ZIP contains exactly one addon folder at root, and the GitHub source ZIP contains the source root contents. ZIP timestamps are normalized.

## What static tests cannot certify

`Polestar.RegisterGuide` with goal coordinates does **not** itself contain a baked terrain walking polyline. The actual arrow and route lines are provided by the currently installed Polestar navigation modules; the full Forge toolchain has private/raw game terrain prerequisites. Do not ship hand-drawn straight-line `Legs.lua` files pretending to be walkable routes. `polestar playtest` and `forge guide lint` require a complete Polestar checkout and Forever data/engine; this standalone source provides validations that do not need either. Real QuestLog and Polestar integration tests remain on the in-game checklist.
