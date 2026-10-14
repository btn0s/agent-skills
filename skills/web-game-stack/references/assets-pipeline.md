# Asset pipeline

Search owned packs through the `owned-assets` skill and local assets CLI before sourcing new content. Keep source packs, extracted files, and purchased textures or models in ignored local directories such as `.asset-cache/` or `assets-owned/`. Commit converters, manifests, mapping tables, and output format contracts; never commit or redistribute purchased content through the skill or engine.

For Unreal packs, export headlessly into a staging directory, convert to GLB with stable names, inspect animation tracks and root scale, and place game-ready output in the game's own asset store. Record the pack and license source in a local manifest without copying credentials or purchase metadata. Validate path case on Windows and Linux. Warm high-cost GLB parse, materials, and animation samplers before revealing the player. Blacksite and ALS submodules may supply their own redistributable demo assets; keep their license files with them.
