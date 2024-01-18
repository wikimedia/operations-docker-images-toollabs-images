#!/usr/bin/env bash
# Rebuild all Docker images in this repo

set -Eeuo pipefail

clean_docker_layers () {
    docker ps --no-trunc -aqf "status=exited" |
        xargs --no-run-if-empty docker rm
    docker images --no-trunc | awk '$2=="<none>" { print $3 }' |
        xargs --no-run-if-empty docker rmi
    docker images -f "dangling=true" -q |
        xargs --no-run-if-empty docker rmi
}

for series in bookworm-sssd bullseye-sssd; do
    echo "=== START toolforge ${series} ==="
    # Clean layers, but ignore errors because the cleaner is a bit sketchy
    clean_docker_layers || /bin/true

    # Build and push the base image first.
    ${PYTHON:-python3} build.py --image-prefix toolforge --tag latest --no-cache --push --single $series ${@}

    # Build and push all dependent images.
    ${PYTHON:-python3} build.py --image-prefix toolforge --tag latest --no-cache --push $series ${@}

    # Clean layers, but ignore errors because the cleaner is a bit sketchy
    clean_docker_layers || /bin/true
    echo "=== END toolforge ${series} ==="
done
