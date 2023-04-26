#!/usr/bin/env python3
"""
Build and publish Docker images.
"""
import argparse
import functools
import itertools
import os
import subprocess
import shutil

import jinja2


# The docker binary to use for executing commands
DOCKER_BINARY = os.environ.get("DOCKER_BINARY", shutil.which("docker"))
# Base path of where the docker images are organized
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Tree of images to be built (identified by filesystem
# paths) and their parents. Leaf nodes are lists while
# everything else is dictionaries. When a particular
# image wants to be rebuilt, all of its parents are too.
# We rely on docker caching to ensure this is not super
# dead slow.
IMAGES = {
    "jessie-sssd": {
        "python2-sssd/base": ["python2-sssd/web"],
        "php5-sssd/base": ["php5-sssd/web"],
        "node6-sssd/base": ["node6-sssd/web"],
        "python34-sssd/base": ["python34-sssd/web"],
        "ruby21-sssd/base": ["ruby21-sssd/web"],
    },
    "stretch-sssd": {
        "python35-sssd/base": ["python35-sssd/web"],
        "golang-sssd/base": ["golang-sssd/web"],
        "jdk8-sssd/base": ["jdk8-sssd/web"],
        "node10-sssd/base": ["node10-sssd/web"],
        "php72-sssd/base": ["php72-sssd/web"],
    },
    "buster-sssd": {
        "golang111-sssd/base": ["golang111-sssd/web"],
        "jdk11-sssd/base": ["jdk11-sssd/web"],
        "php73-sssd/base": ["php73-sssd/web"],
        "python37-sssd/base": ["python37-sssd/web", "python37-sssd/pwb"],
        "ruby25-sssd/base": ["ruby25-sssd/web"],
        "html-sssd/web": [],
    },
    "buster-standalone": [],
    "bullseye-sssd": {
        "jdk17-sssd/base": ["jdk17-sssd/web"],
        "mariadb-sssd/base": [],
        "mono68-sssd/base": [],
        "node12-sssd/base": ["node12-sssd/web"],
        "node16-sssd/base": ["node16-sssd/web"],
        "perl532-sssd/base": ["perl532-sssd/web"],
        "php74-sssd/base": ["php74-sssd/web"],
        "python39-sssd/base": ["python39-sssd/web", "python39-sssd/pwb"],
        "ruby27-sssd/base": ["ruby27-sssd/web"],
        "tcl86-sssd/base": ["tcl86-sssd/web"],
    },
    "bullseye-standalone": [],
    # buildpack stacks
    "bullseye0/base": ["bullseye0/build", "bullseye0/run"],
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


def make_dockerfile(name, registry, image_prefix, tag, jinja_env):
    ctx = {"registry": registry, "image_prefix": image_prefix, "tag": tag}
    tmpl = jinja_env.get_template("{}/Dockerfile.template".format(name))
    dockerfile = tmpl.render(**ctx)
    if dockerfile is None:
        raise RuntimeError("Generated empty Dockerfile for {}".format(name))

    out_file = os.path.join(BASE_PATH, name, "Dockerfile")
    with open(out_file, "wt") as f_out:
        f_out.write(dockerfile)


def rm_dockerfile(name):
    os.unlink(os.path.join(BASE_PATH, name, "Dockerfile"))


def build_image(name, registry, image_prefix, no_cache, tag, jinja_env):
    print("\x1b[32m" + ("#" * 78) + "\x1b[0m")
    print(
        "\x1b[32m  Building {}/{}-{}:{}\x1b[0m".format(
            registry, image_prefix, name, tag
        )
    )
    print("\x1b[32m" + ("#" * 78) + "\x1b[0m")
    make_dockerfile(name, registry, image_prefix, tag, jinja_env)
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
        default="toolforge",
        help=(
            "Prefix to use for each image name to make sure they are easily"
            " differentiable"
        ),
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

    # Setup template engine
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(BASE_PATH),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Separate build and push step so we do not push images if
    # any of them fail
    for image in images:
        build_image(
            image,
            args.docker_registry,
            args.image_prefix,
            args.no_cache,
            args.tag,
            jinja_env,
        )

    if args.push:
        for image in images:
            push_image(image, args.docker_registry, args.image_prefix, args.tag)


if __name__ == "__main__":
    main()
