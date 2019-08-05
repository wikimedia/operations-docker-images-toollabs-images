import build
from nose.tools import assert_equals


def assert_same(result, expect):
    """Check arrays for order-free equality."""
    assert_equals(sorted(result), sorted(expect))


def test_lineage_of():
    build.IMAGES = {
        'base': {
            'A': ['A1', 'A2'],
            'B': ['B1', 'B2'],
            'C': {
                'C1': {'C1a': ['C1a1']},
                'C2': ['C2a'],
            }
        }
    }

    assert_equals(build.lineage_of('not_found'), None)
    assert_same(
        build.lineage_of('base'),
        [
            'base',
            'A', 'A1', 'A2',
            'B', 'B1', 'B2',
            'C', 'C1', 'C1a', 'C1a1', 'C2', 'C2a',
        ]
    )
    assert_same(
        build.lineage_of('B1'),
        ['base', 'B', 'B1']
    )
    assert_same(
        build.lineage_of('C1'),
        ['C1a1', 'C1a', 'C1', 'C', 'base']
    )
    assert_same(
        build.lineage_of('C1a1'),
        ['C1a1', 'C1a', 'C1', 'C', 'base']
    )


def test_make_docker_tag():
    tests = {
        'registry/prefix-name:latest': ['name', 'registry', 'prefix', 'latest'],
        'test/prefix-foo-bar-baz:stable': ['foo/bar/baz', 'test', 'prefix', 'stable'],
    }
    for expect, args in tests.items():
        yield check_make_docker_tag, args, expect


def check_make_docker_tag(given, expect):
    assert_equals(build.make_docker_tag(*given), expect)


def test_expand_template():
    template = "foo:{foo}\nbar:{bar}"
    assert_equals(
        build.expand_template(template, {'foo': 1, 'bar': 2}),
        "foo:1\nbar:2"
    )
    assert_equals(
        build.expand_template(template, {'foo': 1, 'bar': 2, 'baz': 3}),
        "foo:1\nbar:2"
    )
