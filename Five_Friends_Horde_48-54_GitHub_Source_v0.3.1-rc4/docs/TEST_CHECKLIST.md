# v0.3.1-rc4 — live Polestar test checklist

This candidate passes offline structural and Lua registration tests. Use a single tester's client first, then a five-player session. **These checks have not been run in the game.**

## Installation and navigation prerequisites

- [ ] Exit WoW, delete old `PolestarPack_FiveFriends4854`, extract rc4 into `Interface/AddOns/`; restart (not only `/reload`).
- [ ] Confirm Polestar core, Polestar_Nav, Polestar_Nav_EK, and Polestar_Nav_Kalimdor are enabled. Check the AddOns list at character select; confirm no load-on-demand error.
- [ ] Open the Five Friends 48–54 pack: all **13 guides** appear, with chapter 1 Mara preparation and chapter 13 Sunken Temple.
- [ ] Enable guide pins and route lines. Open `/polestar route`. Test arrow to an NPC in the same zone, then to an NPC in another zone; inspect both the map pin and terrain-following walking trail. If no trail, compare to an official Polestar guide and check Nav modules before concluding this pack's data is wrong.
- [ ] For any wrong coordinate, record chapter/step/quest and `/polestar where` while standing at the actual target. Use the built-in `/mappin` system for your own location sharing, not TomTom `/way`.

## Quest acceptance, work, and reward progression

- [ ] Chapter 1: accept *Strange Pylons* from the western pylon, visit all three pylon stops, finish the objective, then return to Mordent. Test **Fragments of the Pylons** at Magram and Gelkis and **Powering the Pylons** separately.
- [ ] Chapter 1: accept *Forlorn Gardens*, perform garden work, reward it, then accept/complete/reward *What They've Done to My Peonies* before *Word of the Woods*.
- [ ] Chapter 2: the pickup goals route to each **exterior quest giver**; the entrance go-to directs to Desolace 35.7,55.5. Inside Maraudon, follow the written colored-wing, five-khan, Celebras, Princess, Rotgrip order (no invented dungeon interior trail).
- [ ] Chapter 3: Ekkal at Azshara 42.0,38.9 offers *The Legashi Threat*. The objective arrow points toward Legashi camp ~61,23 (not Ekkal) until the three counts each reach five, then it returns to Ekkal.
- [ ] Chapter 3: Eitrigg at Orgrimmar 34.3,39.4 offers *The Missing Kor'kron*; the next chapter leads to Nazeer in Brackenwall Village. Belgrom Rockmaul in Orgrimmar 75.2,34.2 receives *Revenge Exacted*.
- [ ] Chapter 4: safely enter **Alcaz Prison**; DO NOT kill The Questioner before every eligible player accepts Mason's *The Man in the Iron Chains*. After getting his key and freeing Mason, travel to Moonbrook inn **upstairs**, retrieve Document Box at 43.4,67.8, THEN complete that chain's reward/turn-in.
- [ ] Chapter 5: do one Jintha'Alor climb and collect the Ancient Egg if the quest is eligible.
- [ ] Chapter 6: four Searing Gorge towers require their authored multistop waypoint visits before the final objective completes.
- [ ] Chapter 8: receive **A Small Pack** from raft quest 3844; open it and separately confirm Large Compass, Curled Map Parchment, Lion-headed Key for quest 3845. The guide must not send directly to Linken before those three objectives are satisfied.
- [ ] Chapter 8: Lost! starts from Spraggle Frock and ends at Ringo; it must not require the follow-up escort.
- [ ] Chapter 11: each Western Plaguelands cauldron requires its keeper key and its intermediate hand-in; no extra unexplained grind bar appears.
- [ ] Chapter 13: Sunken Temple interior altar and statue-circle hand-ins occur inside the instance; ensure the Essence of Eranikus starter item and font reward are done before leaving. A missing interior arrow is a documented limitation.
- [ ] As a group of five, verify shared kill counts, individual drops, and quest availability. Uzer'i's *The Sunken Temple* 3380 may be absent; its optional check must not hold everyone.

## Test result capture

Record: `chapter | step title | quest ID | observed arrow/map destination | actual /polestar where | quest progress behavior | Polestar version | installed Nav modules`. If a core Polestar guide also has no map trail, provide that fact; it points to the navigation layer rather than the Five Friends quest package.
