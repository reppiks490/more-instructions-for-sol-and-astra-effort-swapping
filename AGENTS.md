# Working on AEONFALL

This repository contains authored Fortnite/UEFN source and import assets. Read [README.md](README.md), [the UEFN setup guide](docs/UEFN_STARTER.md), [the playable loop requirements](docs/FIRST_PLAYABLE_LOOP.md), and [source delivery](docs/SOURCE_DELIVERY.md) before changing integration code.

- Preserve the single persistent player root and the immutable profile copy constructor in `verse/persistence/player_profile.verse`. Checked saves must precede irreversible item delivery.
- Mutable gameplay services belong to a running Verse session. Use the existing session accessors; module-scope construction of objects with mutable members can fail on current UEFN releases.
- Transactions must fail as a whole when a class change, reward save, status batch or queue admission is refused. Do not call a mutating service inside a negated failure context: a successful call there is rolled back.
- Input and physical effects must resolve registered runtime identities and authoritative entitlements. A canonical content entry or a triggered graph alone is not proof that an ability was executed.
- Keep native subscriptions and physical objects owned, bounded and cleaned up. Reconcile canonical state when queued cleanup presentation is unavailable.
- Run the repository's AEONFALL Validation and Verse Static workflows for source checks. New first-play guards are in `tools/validate_first_playable_loop.py`; exact-source delivery is checked by `tests/test_source_bundle.py`.
- Python source checks do not compile or run Verse. Record actual editor import, native compiler output and Fortnite Launch Session evidence separately. Never create guessed `.uefnproject`, `.uplugin`, `.umap` or `.uasset` files.
- Follow the supported editor/MCP discovery instructions and inspect advertised schemas before placing devices or writing editor properties. Preserve creator maps before assembly and validate physical bindings before enabling gameplay.

The current change history is [the build change log](docs/BUILD_CHANGE_LOG.md). Update the relevant guide and history in the same change when behavior or setup changes. Review this router whenever the runtime architecture, checked-save API or engine/editor workflow changes.
