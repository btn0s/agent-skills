# Controller → Pawn → Intent

A Controller is a nonphysical producer of Intent. A Pawn is the physical entity with transform, capsule, velocity, and optional ALS animation. Possession connects one Controller to one Pawn; use an exclusive relation, and clear the old Pawn's Intent when possession changes. A player Controller reads actions and control rotation; an AI Controller reads a brain. Both write the same desired move, jump, crouch, sprint, aim, and fire Intent.

Movement consumes Intent at the fixed physics step and drives one Rapier capsule. ALS reads the resulting movement and produces the third-person pose. The camera follows the possessed Pawn. The FPP camera uses the capsule's stable eye position and control rotation; it never follows a bobbing head bone. Render only arms and weapon in FPP. Preserve the ALS third-person body for other viewers and when switching camera. The starter's Operator adapter supplies this seam for one local Pawn; multiplayer adds remote Pawn entities without local input devices.

Inventory and combat use Arsenal's fixed-step weapon runtime. Feed it aim/muzzle vectors from Operator after the camera step, perform collision queries in the host world, and pass accepted damage through server authority. The starter uses an empty arena, so its sample queries report no targets.
