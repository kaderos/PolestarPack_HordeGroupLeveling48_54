# Five Friends — Horde 48–54 (WoW Forever, Polestar)

**Version: 0.3.1-rc4 — candidate for in-game QA, not a validated stable release.**

This community guide is designed for five Horde players following the revised November 21, 2026 leveling plan. Zul'Farrak is already complete. Maraudon is the first dungeon, Alcaz Prison is next, and Sunken Temple is last; the outdoor chapters run between them. Level ranges are descriptions, **not** hard level gates. No mandatory quest grind is added just to reach a title's end level.

## Installing the addon

1. Exit World of Warcraft completely.
2. Delete the previous `World of Warcraft/_forever_/Interface/AddOns/PolestarPack_FiveFriends4854/` folder.
3. Extract **`PolestarPack_FiveFriends4854-v0.3.1-rc4-forever.zip`** into `World of Warcraft/_forever_/Interface/AddOns/`.
4. Verify `Interface/AddOns/PolestarPack_FiveFriends4854/PolestarPack_FiveFriends4854.toc` exists, with `Pack.lua`, `MapFrames.lua`, and `Guides.lua` alongside it. Do not add a second outer folder.
5. Ensure **Polestar** and its navigation modules **Polestar_Nav**, **Polestar_Nav_EK**, **Polestar_Nav_Kalimdor** are installed and enabled. Restart the game and select the desired Five Friends 48–54 chapter in Polestar.
6. In Polestar's map and arrow settings, turn on guide pins and route lines. `/polestar route` reports the next planned stops; `/polestar where` can record a questionable coordinate for correction. A real walking path depends on the **core** nav database; this addon only supplies locations, goals and instructions.

If you are already past chapter 1, manually select your current chapter. Per-player quest-state goals should automatically dismiss goals that you already completed. Use the chapter and the actual quest-log state, **not** the character's precise displayed level, to resume. The group has a 40-slot quest-log capacity; free space ahead of the dungeon preparations.

## What is fixed from 0.3.0-rc3?

- **Separated distant quest stops:** 13 source steps with mismatched locations were split into 34 coherent steps, so objective search areas, quest giver locations, and rewards appear as ordered individual stops. The new guide has **320** steps across 13 chapters.
- **Missing Forever NPC locations:** Eitrigg (95283, Orgrimmar 34.3,39.4), Ekkal (86746, Azshara 42.0,38.9), and Belgrom Rockmaul (91531, Orgrimmar 75.2,34.2). The Legashi hunt now guides to an approximate Azshara 61.0,23.0 camp rather than the quest giver.
- **Real objectives ahead of hand-ins:** Mason's hidden Document Box at Moonbrook inn upstairs, Westfall 43.4,67.8 (quest 96337), plus the three separately tracked items inside Un'Goro's Small Pack (quest 3845). These previously looked like pure delivery quests.
- **Maintains planned quest chains:** 170 accept and 170 turn-in goals; 98 complete, 51 quest-linked kill and 4 collect goals. The Shen'dralas pylons, Jintha'Alor, Searing Gorge towers, Alcaz Questioner and Sunken Temple remain in their required order.
- **Source is rebuildable:** unlike rc3, the authoring script does not depend on old `/mnt/data` paths. The route JSON and previous guide/reference subsets required for reconstruction are bundled in `inputs/`.

## What this cannot guarantee

- **Walking trail polylines are computed by Polestar's navigation engine.** The pack deliberately does not invent `Legs.lua` walking paths, since an ungrounded direct line could go through walls, mountains or water. A core Nav or map-layer problem must be diagnosed in Polestar, not disguised by fake straight lines.
- Exact room coordinates are unavailable for many **Maraudon, Alcaz Prison, and Sunken Temple** bosses/objects. The guide supplies verified **outdoor entrance points and clear written dungeon sequences**, not fictitious interior pathing.
- Some optional starters, including Witch Doctor Uzer'i's *The Sunken Temple* (3380), might not be offered to everyone. The route allows skipping those branches. A quest with no work stage may be a **legitimate courier**, not an objective omission.
- A static Python and Lua registration test does not establish whether a Forever quest, party credit or arrow works live. Read `docs/TEST_CHECKLIST.md` before distributing to all five players.

The original 48–54 route ledger is in `evidence/route-ledger.json`, and the full revised route PDF is `docs/Five_Friends_Horde_48-54_Revised_Route.pdf`. This addon is a separate community pack and does not replace Polestar's own guide or navigation modules.

## Rebuilding the release

From the source package directory on Linux with Python 3.10+ and `liblua5.4-0` installed:

```bash
python3 scripts/rebuild.py
```

This starts from the bundled research sources and regenerates the compiled JSON and LUA, runs structural regression checks, then loads all Lua files with registration stubs. `docs/SOURCE_REBUILD.md` explains the inputs and limitations. To create release ZIPs run `python3 scripts/package_release.py` after rebuilding. On Windows you may run `python scripts/rebuild.py --skip-lua` to validate the authored data and regenerate source without the Linux Lua library, but that does **not** provide Lua execution validation.

**Not published to GitHub/CurseForge.** These files are a tested local release candidate. This source and addon use the original pack's CC0 guide-text attribution, with third-party notices in `LICENSE-DATA.txt`.
