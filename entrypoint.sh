#!/bin/sh
# ============================================================
# WHY THIS FILE EXISTS (read this before touching anything below)
# ============================================================
# Docker has two separate moments in time:
#   1. BUILD TIME  -> when `docker build` / `docker compose up --build` runs.
#                     This is when the IMAGE gets created.
#   2. RUN TIME    -> when the container actually starts and the app runs live.
#
# Dockerfile's `RUN` commands ONLY execute at BUILD TIME, once, and then
# freeze into the image forever. But a named volume (upload/output) gets
# attached to the container LATER, at RUN TIME -- and mounting a volume can
# silently overwrite the folder's ownership/permissions that were set
# during build. So a `RUN chown ...` in the Dockerfile can never fix
# something that only happens after the build is already finished.
#
# This script is the fix: it's the ENTRYPOINT, meaning it runs every single
# time the container STARTS (at run time, after the volume is already
# mounted) -- so it can re-fix ownership/permissions at exactly the right
# moment, every time, no matter what the volume did to them.
#
# Flow: container starts as root -> this script fixes folder permissions
# -> script switches down to appuser -> THEN the real app (CMD from
# Dockerfile) finally runs, as appuser, with correct folder access.
# ============================================================


# Make appuser the owner of the volume-backed folders (fixes root-owned
# volumes on mount).
chown -R appuser:appuser /app/uploads /app/output

# Lock permissions down: owner=full access, group=read/execute, others=none.
# (Not 777 -- that would let ANY user/process write here, which defeats
# the point of having a non-root user in the first place.)
chmod -R 750 /app/uploads /app/output

# Drop from root -> appuser, then run whatever CMD the Dockerfile specified
# (passed in here as "$*"). `exec` replaces this script's process instead
# of spawning a new one -- keeps Ctrl+C / stop signals working correctly.
exec su -s /bin/sh appuser -c "$*"