#!/usr/bin/env bash
# Rebuild all Docker images in this repo

set -Eeuo pipefail

clean_docker_layers () {
    docker ps --no-trunc -aqf "status=exited" | xargs docker rm
    docker images --no-trunc | awk '$2=="<none>" { print $3 }' |
        xargs -r docker rmi
    docker images -f "dangling=true" -q |
        xargs -r docker rmi
}

for series in base stretch; do
    # Images for the legacy k8s cluster
    ./build.py --image-prefix toollabs --tag latest --no-cache --push $series
    clean_docker_layers
done

for series in jessie-sssd stretch-sssd buster buster-sssd; do
    # Images for the 2020 k8s cluster
    ./build.py --image-prefix toolforge --tag latest --no-cache --push $series
    clean_docker_layers
done
