# VFX and audio

Treat impact, footstep, fire, reload, and destruction effects as presentation events emitted after simulation. Use pooled particles, instanced meshes, and bounded audio voices. Distinguish predicted local fire effects from server-accepted damage events so a rejected shot never applies health loss. Attach ALS footstep sound to its character sink and unlock browser audio from a user gesture. Fade or stop voices on room disposal.

Keep audio samples and purchased VFX content in the game's ignored asset pipeline. Shared Blacksite packages expose events and adapters; the game chooses sounds, art direction, and mix. Warm shaders and common impact effects before the first interactive frame where possible.
