#!/usr/bin/env python3
"""
Build and publish Docker images.
"""
import argparse
import os
import subprocess


# The docker binary to use for executing commands
DOCKER_BINARY = os.environ.get('DOCKER_BINARY', '/usr/bin/docker')
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
        ],
        'java/base': [
            'java/web',
        ],
        'static-web': [],
    },
}


def make_docker_tag(name, registry, image_prefix):
    return '{registry}/{prefix}-{sanitized_name}'.format(
        registry=registry,
        prefix=image_prefix,
        sanitized_name=name.replace('/', '-')
    )


def make_dockerfile(name, registry, image_prefix):
    image_dir = os.path.join(BASE_PATH, name)
    template_file = os.path.join(image_dir, 'Dockerfile.template')
    out_file = os.path.join(image_dir, 'Dockerfile')
    kwargs = {'registry': registry, 'image_prefix': image_prefix}
    with open(template_file, 'rt') as f_in:
        with open(out_file, 'wt') as f_out:
            for line in f_in:
                f_out.write(expand_template(line, kwargs))


def rm_dockerfile(name):
    os.unlink(os.path.join(BASE_PATH, name, 'Dockerfile'))


def build_image(name, registry, image_prefix, no_cache):
    make_dockerfile(name, registry, image_prefix)
    args = [
        DOCKER_BINARY,
        'build',
        '-t', make_docker_tag(name, registry, image_prefix),
    ]
    if no_cache:
        args.append('--no-cache')
    args.append(os.path.join(BASE_PATH, name))
    subprocess.check_call(args)
    rm_dockerfile(name)


def push_image(name, registry, image_prefix):
    subprocess.check_call([
        DOCKER_BINARY,
        'push',
        make_docker_tag(name, registry, image_prefix)
    ])


def lineage_of(name):
    def children_of(node):
        if type(node) == dict:
            children = list(node.keys())
            for k, v in node.items():
                children += children_of(v)
            return children
        return node

    def ancestors_of(node, cur_lineage):
        if name in node:
            cur_lineage.append(name)
            if type(node) == dict:
                cur_lineage.extend(children_of(node[name]))
            return cur_lineage

        if type(node) == dict:
            for k, v in node.items():
                ret = ancestors_of(v, cur_lineage + [k])
                if ret:
                    return ret
        return None

    return ancestors_of(IMAGES, [])


def expand_template(template, params):
    return template.format(**params)


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
    argparser.add_argument(
        '--no-cache',
        action='store_true',
        help="Do not use docker's cache when building images, build from scratch"
    )

    args = argparser.parse_args()
    images = lineage_of(args.image)
    print('Building following images: ', images)

    # Separate build and push step so we do not push images if
    # any of them fail
    for image in images:
        build_image(image, args.docker_registry, args.image_prefix, args.no_cache)

    if args.push:
        for image in images:
            push_image(image, args.docker_registry, args.image_prefix)

if __name__ == '__main__':
    main()
