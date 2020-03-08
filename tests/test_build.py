import os
import pytest
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import build  # noqa


def assert_same(result, expect):
    """Check arrays for order-free equality."""
    assert sorted(result) == sorted(expect)


def test_lineage_of():
    build.IMAGES = {
        "base": {
            "A": ["A1", "A2"],
            "B": ["B1", "B2"],
            "C": {"C1": {"C1a": ["C1a1"]}, "C2": ["C2a"]},
        }
    }

    assert build.lineage_of("not_found") is None
    assert_same(
        build.lineage_of("base"),
        [
            "base",
            "A",
            "A1",
            "A2",
            "B",
            "B1",
            "B2",
            "C",
            "C1",
            "C1a",
            "C1a1",
            "C2",
            "C2a",
        ],
    )
    assert_same(build.lineage_of("B1"), ["base", "B", "B1"])
    assert_same(build.lineage_of("C1"), ["C1a1", "C1a", "C1", "C", "base"])
    assert_same(build.lineage_of("C1a1"), ["C1a1", "C1a", "C1", "C", "base"])


@pytest.mark.parametrize(
    "expect,args",
    (
        (
            "registry/prefix-name:latest",
            ["name", "registry", "prefix", "latest"],
        ),
        (
            "test/prefix-foo-bar-baz:stable",
            ["foo/bar/baz", "test", "prefix", "stable"],
        ),
    ),
)
def test_make_docker_tag(expect, args):
    assert build.make_docker_tag(*args) == expect
