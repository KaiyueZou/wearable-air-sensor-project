# Using the GLB on a static website

A static site can host this GLB and an interactive WebGL viewer. With an appropriate viewer, visitors can drag to rotate/orbit the sensor and zoom. The GLB is the model asset; an HTML page or viewer integration supplies controls, lighting, camera framing and accessibility.

The included model contains 51 hardware meshes, two primary measurement/scatter paths and 15 enlarged particles at source frame 721. It is a frozen illustrative state, not an animated sensor simulation. Displaying light paths does not validate optical power, wavelength, particle sizing or safety. Keep those caveats visible near a future viewer.

A future integration can use a maintained glTF viewer, such as Google's `<model-viewer>` web component or Three.js. Configure orbit controls, useful zoom bounds and a poster image such as `media/tour-contact-sheet.jpg`. Serve over HTTP(S), verify MIME and cross-origin settings, and test touch, keyboard/fallback access and mobile performance. Review any external runtime's license and privacy implications before deploying.

This repository contains no web app or deployment, and selecting/configuring a viewer remains separate work.
