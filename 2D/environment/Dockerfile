FROM python:3.11.9-slim-bookworm@sha256:8fb099199b9f2d70342674bd9dbccd3ed03a258f26bbd1d556822c6dfc60c317

LABEL org.opencontainers.image.title="NR Spatial 2D CPU environment"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONNOUSERSITE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    JUPYTER_PREFER_ENV_PATH=1 \
    MPLCONFIGDIR=/home/vscode/.cache/matplotlib \
    OPENBLAS_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git procps libstdc++6 ca-certificates \
    && mkdir -p /usr/local/share/nr2d \
    && dpkg-query -W > /usr/local/share/nr2d/system-packages.tsv \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash vscode \
    && git config --system --add safe.directory /workspaces/NR-object-state

COPY requirements-container.txt /usr/local/share/nr2d/requirements-container.txt
RUN python -m pip install --no-cache-dir --require-hashes \
        -r /usr/local/share/nr2d/requirements-container.txt \
    && python -m pip check \
    && python -m ipykernel install --sys-prefix --name nr-spatial-state \
        --display-name "NR 2D (Docker)" \
    && python -c "from pathlib import Path; import sysconfig; Path(sysconfig.get_paths()['purelib'], 'nr2d-source.pth').write_text('/workspaces/NR-object-state/2D/src\n')"

USER vscode
WORKDIR /workspaces/NR-object-state/2D
CMD ["sleep", "infinity"]
