# Tablet Clank — one-shot collector image.
#
# Digest-pinned base (same digest feature-phone-clank pins; verified there),
# non-root user, no pip install of the package (the zero-dependency package is
# carried on PYTHONPATH so path math stays identical to a source checkout). An
# external scheduler (systemd timer or cron) invokes this image repeatedly with
# `production` / `soak` / `collect`; the container itself schedules nothing.
FROM python:3.12-slim-bookworm@sha256:a116514e19457bcb7af7efe9c3dd0b9b71e85b317694e7882a1c52aa15a78134

ARG GIT_REVISION=unknown
LABEL org.opencontainers.image.revision="${GIT_REVISION}"
LABEL org.clank.clank_id="tablet-clank"
LABEL org.clank.data_role="persistent"

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    TABLET_CLANK_SOURCE_REVISION=${GIT_REVISION} \
    TABLET_CLANK_DB=/app/data/tablet_clank.db

RUN groupadd --gid 10001 clank && useradd --uid 10001 --gid clank --create-home clank

WORKDIR /app
COPY --chown=clank:clank tablet_clank/ ./tablet_clank/
COPY --chown=clank:clank migrations/ ./migrations/

# Runtime state lives exclusively in the mounted volume, never in the tree.
RUN mkdir -p /app/data && chown -R clank:clank /app/data
USER clank

HEALTHCHECK --interval=5m --timeout=30s \
  CMD ["python", "-m", "tablet_clank.cli", "db-integrity", "--db", "/app/data/tablet_clank.db"]

ENTRYPOINT ["python", "-m", "tablet_clank.cli"]
CMD ["production", "--db", "/app/data/tablet_clank.db"]
