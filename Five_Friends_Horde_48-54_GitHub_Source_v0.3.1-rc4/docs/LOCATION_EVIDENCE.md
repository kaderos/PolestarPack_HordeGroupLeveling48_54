# Quest location provenance (rc4)

**Newly confirmed in 2026-11-21 lookup:**

- Quest 95283, *The Missing Kor'kron*: start Eitrigg, **Orgrimmar 34.3,39.4** (UI Map 1454), end Nazeer Bloodpike, Dustwallow 35.2,30.7. References: [Icy Veins Forever DB](https://db.icy-veins.com/wow-forever/quests/95283), [Forever XP](https://forever-xp.com/quests/95283/), [Wowhead Forever](https://www.wowhead.com/forever/quest=95283).
- Quest 86746, *The Legashi Threat*: start/end Ekkal, **Azshara 42.0,38.9** (UI Map 1447); objective camp near **Azshara 61,23**. Five Legashi Satyrs, five Rogues, five Hellcallers. References: [Zephras Forever quest](https://zephras.com/forever/enUS/quest/86746/), [Forever XP](https://www.forever-xp.com/quests/86746/), [Wowhead Forever](https://www.wowhead.com/forever/quest=86746).
- Quest 91531, *Revenge Exacted*: turn-in Belgrom Rockmaul, **Orgrimmar 75.2,34.2** (UI Map 1454). References: [Zephras Forever quest](https://zephras.com/forever/enUS/quest/91531/), [Forever XP](https://www.forever-xp.com/quests/91531/).
- Quest 96337, *More Valuable Than Gold*: the revised research ledger and [Wowhead Alcaz toy walkthrough](https://www.wowhead.com/forever/guide/alcaz-operative-disguise-toy-secret-walkthrough) identify the Loose Floorboards/Connery's Trunk upstairs in the Moonbrook inn, **Westfall 43.4,67.8** (UI Map 1436); this is a **known location in the prior authored quest reward**, but the client interaction and quest-complete state must still be confirmed live.
- Quest 3845, *It's a Secret to Everybody*: recovered objective item IDs and counts from the checked-in `inputs/ref49/reference/quests.json`; *Large Compass* 11104, *Curled Map Parchment* 11105 and *Lion-headed Key* 11106. The Small Pack comes from the prior raft quest around Un'Goro 63.1,69.1. No additional coordinate needed for bag inventory objectives.

**Historical rc3 data:**

- `inputs/prev/guides/`: prior Five Friends 43–48 1.2.1 authored coordinates, comments and ordering.
- `inputs/ref49/`: prior Five Friends 49–54 1.0.0 compiled quest and NPC cache, source revision in `inputs/ref49/reference/PROVENANCE.json`.
- `evidence/route-ledger.json`: revised 48–54 plan, including original quest sources and exact reward chapter ordering.

**Known gaps:**

- Maraudon, Alcaz Prison, and Sunken Temple interior portal/room coordinates cannot be relied upon to generate terrain-following dungeon navigation. The pack uses entrance approach goals and descriptive clear sequencing instead of invented indoor floor pins.
- The Legashi camp coordinate is a broad **quest-objective search area**, not a guaranteed individual satyr spawn.
- Coordinates may differ by map frame or newly updated Forever server state. Record exact `/polestar where` standing beside the true NPC or object during testing, then fix its original authored data.

Quest tracking, party credit and optional quest availability still require client testing. These are locations researched for authoring purposes, not observation of five live players.
