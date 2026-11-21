# Five Friends: Horde 48–54 (release candidate)

A 13-chapter Polestar community addon based on the November 21 revised route. **This release candidate is NOT fully quest-automated.** It presents the verified planning instructions and quest reward checklist as manually acknowledged tasks. Do not publish as a stable release until the Polestar client registration and quest-tracking goals are tested.

## Install

Extract the release ZIP directly into `World of Warcraft/_forever_/Interface/AddOns/`. It contains a single `PolestarPack_FiveFriends4854` directory. Enable the addon and Polestar; run `/polestar packs` and check that 13 guides are registered.

## Play

The group has already cleared Zul'Farrak; Maraudon preparation is chapter 01, Maraudon chapter 02, Alcaz chapter 04, Sunken Temple chapter 13. The level ranges are estimates, not grind gates. Every player has 40 quest-log slots. Each manual checkpoint must be acknowledged after the whole party finishes it. Check the source `plan/route.json` for the full quest ledger and optional starter watchlist.

## Limitations

- Guide checkpoints use manual tasks rather than Polestar's automatic quest-state API.
- This is a pre-release candidate, not yet tested in the live game.
- No automatic GitHub release was created or published.
