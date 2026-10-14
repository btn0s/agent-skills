# Pins and exceptions

Default: use the latest published version in a caret range for every generated dependency. Refresh ranges when scaffolding; avoid exact versions in package manifests. The scaffold sets `minimumReleaseAge: 0` in its pnpm workspace because the requested latest range can include a release newer than pnpm’s default age filter; review fresh lockfile changes before promoting a build. Submodule pointers are Git identities, not npm dependency pins, and must be reachable from their remotes.

One documented exception: Blacksite Rupture ships a patched Rapier build at `0.19.2-rupture.4` for applied impulses and structural physics. Rupture alone consumes its local patched tarballs. Ordinary game physics uses stock Rapier. Keep the patch, build recipe, and reason in Blacksite; do not copy the tarballs into this skill. Re-evaluate the exception only after a compatible upstream release reproduces Rupture's conservation and replay invariants.

An old `@react-three/rapier` world-free patch remains a behavior to verify, not an automatic version pin. An old exact `postprocessing` range has no verified exception and should use a caret range.
