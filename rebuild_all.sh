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

for series in jessie-sssd stretch-sssd buster-sssd; do
    # Images for the 2020 k8s cluster
    echo "=== START toolforge ${series} ==="
    ./build.py --image-prefix toolforge --tag latest --no-cache --push $series
    clean_docker_layers || /bin/true
    echo "=== END toolforge ${series} ==="
done
