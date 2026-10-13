# Console UI and input

Blacksite `input` owns actions, evaluators, device observations, glyphs, touch adapters, and spatial console navigation. Blacksite `ui` supplies the Base UI / Tailwind v4 console components. Import these packages as workspace source packages when a menu, inventory, settings, or lobby is built. Do not copy an older omni-input implementation into the game.

Map keyboard, gamepad, pointer, and touch devices to semantic actions in one place. Gameplay reads actions or Intent; menus read navigation actions. Console focus moves spatially by direction rather than browser tab order. Use at least 44 px targets and visible selected/active states designed for couch distance. Preserve an accessible equivalent for users who need keyboard or assistive navigation even if the game surface suppresses default tab outlines.

Keep device listeners in scoped lifetimes. On blur, pointer-lock loss, disconnection, and possession changes, clear held movement, aim, and fire edges. Avoid auto-repeat creating new jump/reload edges. The included FPP starter uses Operator's classic input adapter as a minimal playable seed; migrate the game's action map to `@blacksite/input` when expanding controls.
