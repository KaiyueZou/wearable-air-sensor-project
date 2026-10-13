# Release validation

Validated on 2026-10-13 with Blender 4.3.2, Python 3.12.14, Pillow 12.3.0, NumPy 2.3.5, SciPy 1.17.0 and FFmpeg 7.1.5 on Linux. macOS instructions are provided but macOS was not exercised.

## Passed

- Exact release ZIP extracted into a fresh directory whose path contains spaces; commands ran from an unrelated working directory.
- Release manifest and SHA-256 checks passed, including with an in-repository `.venv` marker matching the documented setup.
- All three MP4s match accepted source bytes. All video frames were decoded: 4,176 film frames / 174 seconds, 480 tour frames / 32 seconds, 320 watch frames / 20 seconds. Dimensions, H.264 encoding, frame rates and absence of audio match the release configuration.
- Current GLB matches the accepted revised export bytes: 51 hardware meshes, two primary optical paths, 15 illustrative particles, no camera or animation tracks.
- All three repacked Blender files decompress to byte-identical original scene data.
- Film builder ran successfully from its retained v3 source dependency.
- Watch builder and preparation ran successfully; exact meshes and local transforms of all 51 accepted sensor hardware objects match.
- Fresh smoke test rendered film indices 0 and 1008, generated optical depth masks, and applied its compositor.
- Fresh tour smoke generated complete orbit projection metadata and global smooth label trajectories, rendered a native base frame and applied labels.
- Watch frame 145 rendered natively. GLB export and independent Blender import verified all 68 named meshes.
- All three pipeline dry runs passed. Invalid-index and missing-frame guards were checked.
- Relative documentation links, source completeness, shared font notices and absence of machine-specific paths in executable source were checked.

## Scope limits

This release did **not** rerender all 4,976 native film/tour/watch frames or regenerate both complete GIF loops. Approved full MP4s are preserved and decoded instead. Existing GIF validation records and source-output hashes are retained; the large GIFs are optional generated outputs. Representative smoke tests verify executable source paths without implying a full visual-regression pass.

The simulations and visual checks do not establish optical accuracy, calibration, health claims, enclosure/water resistance, manufacturability or eye safety. The model remains an illustrative concept.

## Publication preparation

The current release additionally includes both original GIFs and sanitized relative path fields in the three Blender scenes. Current hashes supersede the pre-publication scene hashes above. See [PUBLICATION_AUDIT.md](PUBLICATION_AUDIT.md) for checks and limitations; prior Blender rendering results are historical, not a claim of a post-cleanup rerender.
