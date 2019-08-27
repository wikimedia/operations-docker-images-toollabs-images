#!/usr/bin/env python3
"""
Build and publish Docker images.
"""
import argparse
import functools
import itertools
import os
import subprocess


# The docker binary to use for executing commands
DOCKER_BINARY = os.environ.get("DOCKER_BINARY", "/usr/bin/docker")
# Base path of where the docker images are organized
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Tree of images to be built (identified by filesystem
# paths) and their parents. Leaf nodes are lists while
# everything else is dictionaries. When a particular
# image wants to be rebuilt, all of its parents are too.
# We rely on docker caching to ensure this is not super
# dead slow.
IMAGES = {
    "base": {
        "php/base": ["php/web"],
        "static-web": [],
        "nodejs/base": ["nodejs/web"],
        "python2/base": ["python2/web"],
        # Python refers to python3, because it is 2016!
        "python/base": ["python/web"],
        "ruby/base": ["ruby/web"],
    },
    "stretch": {
        "golang/base": ["golang/web"],
        "jdk8/base": ["jdk8/web"],
        "node10/base": ["node10/web"],
        "php72/base": ["php72/web"],
        "python35/base": ["python35/web"],
        "tcl/base": ["tcl/web"],
    },
    "trusty-legacy": {},
}

# Unbuffer print output (https://stackoverflow.com/a/40161931/8171)
print = functools.partial(print, flush=True)


def make_docker_tag(name, registry, image_prefix, tag):
    return "{registry}/{prefix}-{sanitized_name}:{tag}".format(
        registry=registry,
        prefix=image_prefix,
        sanitized_name=name.replace("/", "-"),
        tag=tag,
    )


def make_dockerfile(name, registry, image_prefix):
    image_dir = os.path.join(BASE_PATH, name)
    template_file = os.path.join(image_dir, "Dockerfile.template")
    out_file = os.path.join(image_dir, "Dockerfile")
    kwargs = {"registry": registry, "image_prefix": image_prefix}
    with open(template_file, "rt") as f_in:
        with open(out_file, "wt") as f_out:
            for line in f_in:
                f_out.write(expand_template(line, kwargs))


def rm_dockerfile(name):
    os.unlink(os.path.join(BASE_PATH, name, "Dockerfile"))


def build_image(name, registry, image_prefix, no_cache, tag):
    print("\x1b[32m" + ("#" * 78) + "\x1b[0m")
    print(
        "\x1b[32m  Building {}/{}-{}\x1b[0m".format(
            registry, image_prefix, name
        )
    )
    print("\x1b[32m" + ("#" * 78) + "\x1b[0m")
    make_dockerfile(name, registry, image_prefix)
    args = [
        DOCKER_BINARY,
        "build",
        "-t",
        make_docker_tag(name, registry, image_prefix, tag),
    ]
    if no_cache:
        args.append("--no-cache")
    args.append(os.path.join(BASE_PATH, name))
    subprocess.check_call(args)
    rm_dockerfile(name)


def push_image(name, registry, image_prefix, tag):
    subprocess.check_call(
        [
            DOCKER_BINARY,
            "push",
            make_docker_tag(name, registry, image_prefix, tag),
        ]
    )


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
        "image",
        help="Which image to build. Will also build all ancestors + descendents of image",
        choices=list(
            itertools.chain(*[lineage_of(base) for base in IMAGES.keys()])
        ),
    )
    argparser.add_argument(
        "--push",
        action="store_true",
        help="Push the images to the repository afterwards",
    )
    argparser.add_argument(
        "--docker-registry",
        default="docker-registry.tools.wmflabs.org",
        help="Name of docker registry to tag images with & push to",
    )
    argparser.add_argument(
        "-t",
        "--tag",
        default="testing",
        help=(
            "Tag for this image.  "
            "The default is testing and other options is latest.  "
            "Latest is what should be shipped to webservice."
        ),
        type=str,
        choices=["latest", "testing"],
    )
    argparser.add_argument(
        "--image-prefix",
        default="toollabs",
        help="Prefix to use for each image name to make sure they are easily differntiable",
    )
    argparser.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not use docker's cache when building images, build from scratch",
    )
    argparser.add_argument(
        "--single",
        "-s",
        action="store_true",
        help="Build only a single image rather than full chain",
    )

    args = argparser.parse_args()
    if args.single:
        images = (args.image,)
    else:
        images = lineage_of(args.image)
    print("Building following images: ", images)

    # Separate build and push step so we do not push images if
    # any of them fail
    for image in images:
        build_image(
            image,
            args.docker_registry,
            args.image_prefix,
            args.no_cache,
            args.tag,
        )

    if args.push:
        for image in images:
            push_image(image, args.docker_registry, args.image_prefix, args.tag)


if __name__ == "__main__":
    main()
