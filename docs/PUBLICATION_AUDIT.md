# Publication audit — October 13, 2026

The ZIP was preserved separately. This checkout excludes macOS Finder metadata and resource forks. No original ZIP, caches, local environment, Git history, or personal contact details are included.

## Inspection and cleanup

- Reviewed all project text/code and release records for private paths, owner contact details, and credential patterns. No confirmed credentials or private contact details were found.
- Decompressed all three Blender scenes; parsed every block with bounds checks and examined embedded printable metadata. Removed 23 historical build-machine/path fields, replacing them with null-padded relative paths without changing block sizes, geometry, animation, or other data. Recompression was verified by decompression and exact comparison with the sanitized data. Packed font resources and their required third-party notices remain intact.
- Reviewed the GLB asset metadata, names, and all custom extras. It is self-contained and has no external resource URIs; it contains 68 meshes and no camera or animation tracks.
- Inspected JPEG EXIF, GIF metadata, and all MP4 container/stream tags. No location, owner contact, private paths, or account metadata was found. GIFs and videos preserve their original bytes.
- Decoded all three MP4s with FFmpeg and inspected the supplied visual contact sheets. Reviewed the two GIFs and their metadata. These are concept diagrams and watch illustrations, not personal footage.
- Updated GIF inclusion, release inventory, scene hashes, manifest, and checksum records to describe the actual public package. Third-party attribution, notices, and the existing no-blanket-license rights statement remain.

## Verification limits

Blender is not installed in the publication environment. This audit verifies the scene containers, path-only byte changes, and preserved data, but does not claim that the sanitized scenes were opened or rerendered in Blender. The earlier rendering checks in VALIDATION.md describe the supplied release before metadata cleanup. No complete rerender or new scientific validation was performed.

Pattern scans and metadata inspection are not a proof against every possible hidden payload; no unresolved personal-information finding remained in the reviewed publication files. The public repository account and commit attribution identify its owner intentionally; commits use GitHub's noreply email.
