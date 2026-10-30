# Local pilot runner image. For production, use a separately managed and hardened runner service.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-minimal openjdk-21-jdk-headless g++ ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 runner \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin runner
WORKDIR /workspace
USER 10001:10001
ENV HOME=/tmp
CMD ["/bin/sh"]
