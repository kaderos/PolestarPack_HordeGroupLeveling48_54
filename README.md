# Five Friends Horde 48–54 — automatic quest goals

Release candidate 0.2.0-rc2. This replaces the manually acknowledged quest steps in v0.1.0-rc1 with Polestar native `accept`, `complete` and `turnin` goals. Route text is attached to the active quest step, not a manual blocking task.

Install the addon directory in `_forever_/Interface/AddOns/` and restart WoW. Do not install both v0.1.0 and v0.2.0 under distinct folders; overwrite the `PolestarPack_FiveFriends4854` directory.

**Warning:** This is statically validated, not in-game tested. Complex chain transitions may need corrections; report any quest where an accept goal remains blocked after its predecessor is rewarded. Some quests already accepted or completed in previous chapters can be automatically skipped.

## Rebuild from GitHub source

Run `python scripts/build_auto.py` at the repository root. It reads `source/rc1-Guides.lua` and `evidence/route-ledger.json`, regenerates `addon/PolestarPack_FiveFriends4854/Guides.lua`, and refreshes the distributable ZIP. This script is included for auditability; Polestar Forge compilation and in-game validation remain separate.
