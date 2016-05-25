#!/usr/bin/python3
import subprocess
import os
import argparse


# The docker binary to use for executing commands
DOCKER_BINARY = '/usr/bin/docker'
# Base path of where the docker images are organized
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Tree of images to be built (identified by filesystem
# paths) and their parents. Leaf nodes are lists while
# everything else is dictionaries. When a particular
# image wants to be rebuilt, all of its parents are too.
# We rely on docker caching to ensure this is not super
# dead slow.
IMAGES = {
    'base': {
        'php/base': [
            'php/web',
        ]
    }
}


def make_docker_tag(name, registry, image_prefix):
    return '{registry}/{prefix}-{sanitized_name}'.format(
        registry=registry,
        prefix=image_prefix,
        sanitized_name=name.replace('/', '-')
    )


def build_image(name, registry, image_prefix):
    subprocess.check_call([
        DOCKER_BINARY,
        'build',
        '-t',
        make_docker_tag(name, registry, image_prefix),
        os.path.join(BASE_PATH, name)
    ])


def push_image(name, registry, image_prefix):
    subprocess.check_call([
        DOCKER_BINARY,
        'push',
        make_docker_tag(name, registry, image_prefix)
    ])


def lineage_of(name):
    def children_of(val):
        if type(val) == dict:
            children = list(val.keys())
            for k, v in val.items():
                children += children_of(v)
            return children
        return val

    def ancestors_of(val, cur_lineage):
        if name in val:
            return cur_lineage + children_of(val)
        if type(val) == dict:
            for k, v in val.items():
                ret = ancestors_of(v, cur_lineage + [k])
                if ret:
                    return ret
        return None

    return ancestors_of(IMAGES, [])


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'image',
        help='Which image to build. Will also build all ancestors + descendents of image',
        choices=lineage_of('base')
    )
    argparser.add_argument(
        '--push',
        action='store_true',
        help='Push the images to the repository afterwards'
    )
    argparser.add_argument(
        '--docker-registry',
        default='docker-registry.tools.wmflabs.org',
        help='Name of docker registry to tag images with & push to'
    )
    argparser.add_argument(
        '--image-prefix',
        default='toollabs',
        help='Prefix to use for each image name to make sure they are easily differntiable',
    )

    args = argparser.parse_args()
    images = lineage_of(args.image)
    print('Building following images: ', images)

    # Separate build and push step so we do not push images if
    # any of them fail
    for image in images:
        build_image(image, args.docker_registry, args.image_prefix)

    if args.push:
        for image in images:
            push_image(image, args.docker_registry, args.image_prefix)

if __name__ == '__main__':
    main()
