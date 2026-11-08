# Linux build backend. SDKs are mounted at runtime and are never copied here.
ARG BASE_IMAGE=debian:bookworm-slim@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc
FROM ${BASE_IMAGE}
ARG DEBIAN_SNAPSHOT=20261104T000000Z
ARG PRC_TOOLS_REPO=https://github.com/mozzwald/prc-tools-remix.git
ARG PRC_TOOLS_REV=db9a91d746bac4c5921e3786c39b5dc3eca7b83c
ARG PILRC_REPO=https://github.com/mozzwald/pilrc.git
ARG PILRC_REV=981f88186a1aee57c4c19adc5c497016f01a4743
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s/ bookworm main\ndeb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/%s/ bookworm-security main\n' "$DEBIAN_SNAPSHOT" "$DEBIAN_SNAPSHOT" > /etc/apt/sources.list && \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends autoconf automake bison build-essential ca-certificates flex g++ gcc git gperf libncurses-dev make pkg-config texinfo && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/src
RUN git clone "$PRC_TOOLS_REPO" prc-tools && cd prc-tools && git checkout --detach "$PRC_TOOLS_REV" && ./tools/build.sh /opt/palmdev-toolchain && git clone "$PILRC_REPO" /opt/src/pilrc && cd /opt/src/pilrc && git checkout --detach "$PILRC_REV" && cd unix && autoreconf -fi && ./configure --prefix=/opt/palmdev-toolchain && make -j"$(nproc)" && make install && rm -rf /opt/src
# prc-tools' GCC was built for a /usr prefix. Keep the toolchain local while
# providing the target runtime locations it embeds in its driver search paths.
RUN ln -s /opt/palmdev-toolchain/usr/m68k-palmos /usr/m68k-palmos && ln -s /opt/palmdev-toolchain/usr/arm-palmos /usr/arm-palmos
ENV PATH=/opt/palmdev-toolchain/usr/m68k-palmos/bin:/opt/palmdev-toolchain/usr/arm-palmos/bin:/opt/palmdev-toolchain/usr/bin:/opt/palmdev-toolchain/bin:$PATH GCC_EXEC_PREFIX=/opt/palmdev-toolchain/usr/lib/gcc-lib/ LIBRARY_PATH=/opt/palmdev-toolchain/usr/m68k-palmos/lib
WORKDIR /work
CMD ["/bin/sh"]
