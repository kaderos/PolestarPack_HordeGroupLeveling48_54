# v0.3.1-rc4 — candidate release notes

**Date:** November 21, 2026
**Status:** candidate for in-game navigation testing, NOT confirmed stable.

### Repaired behavior

The guide now distinguishes two physical work chains that the previous build treated as direct deliveries: (1) the fixed Loose Floorboards/Connery's Trunk and Document Box at Moonbrook, Westfall 43.4,67.8 and (2) the three separately tracked items in A Small Pack from Un'Goro's raft. It adds independently checked start/end coordinates for Eitrigg, Ekkal and Belgrom, and a proper search area for Legashi kills. Distant objective/reward goals that were combined within individual steps have been split into separate travel stops (13 source steps split into 34 steps).

### What's included

| Statistic | v0.3.0-rc3 | v0.3.1-rc4 |
| --- | ---: | ---: |
| Linked chapters | 13 | 13 |
| Authored guide steps | 297 | 320 |
| Distinct rewarded quests | 170 | 170 |
| Quest pickup goals | 170 | 170 |
| Quest turn-in goals | 170 | 170 |
| Quest completion goals | 97 | 98 |
| Quest-linked kill goals | 51 | 51 |
| Quest-linked collect goals | 1 | 4 |
| Source-defined multistop / approach waypoints | 37 | 37 |
| Mapped goal entries (including authored waypoints) | 482 | 487 |

The 13%-bonus XP projection, Maraudon-first → Alcaz → Sunken Temple order, 40-slot quest-log constraint, and chapter reward allocations remain unchanged from the revised plan.

### Important dependency

**A location is not a baked walk.** Polestar maps and direction arrows require the Polestar addon and `Polestar_Nav`, `Polestar_Nav_EK` and `Polestar_Nav_Kalimdor`. These modules generate the actual in-game path. This release supplies target quest coordinates and ordered work stages; it does not encode possibly unsafe fabricated pathlines. Indoor dungeon floor maps and live party completion still require field verification.

### Verification performed

- Original rc3 ZIP hashes verified against rc3 SHA256SUMS, then source inspected.
- Complete source rebuilt without historical filesystem paths; deterministic outputs and standalone re-extraction checked.
- 13 connected guides; 170 unique reward quests; 170 pickups; all modeled work precedes its relevant turn-in; all chapters fit Polestar's 60-step cap.
- Corrected quest-specific coordinates verified in compiled JSON, Lua, and installer.
- Lua files loaded with a Lua 5.4 stub defining the published Polestar registrations, without runtime exceptions.

### Not performed

- **No WoW Forever executable/client access, no actual waypoint arrow or painted trail observation, no real quest acceptance or kill-credit test, and no live party/dungeon tests.**
- No Forge `guide lint` / `polestar playtest` using a full local Polestar game database (the release rebuild validates the shipped format-5 payload without that installation).
- No GitHub release upload. The workflow in the source can publish it after a user pushes a version tag to their own repository.
