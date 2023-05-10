from unittest.mock import patch
from pathlib import Path
from expects import *
import pytest

from hnelib.runner import Runner, Item, Expansion, PlotExpansion, MultipleExpansionsFound

class TestRunner:
    def test_parse_collection(self):
        func = lambda: print(1)

        runner = Runner(
            collection={
                'test': func
            }
        )

        expected = [Item(do=func, path_components=['test'])]
        actual = runner.items

        expect(actual).to(equal(expected))

    def test_nested_item(self):
        func = lambda: print(1)

        runner = Runner(
            collection={
                'dir1': {
                    'subdir1': {
                        'do': func,
                    },
                },
            }
        )

        expected = [Item(do=func, path_components=['dir1', 'subdir1'])]

        expect(runner.items).to(equal(expected))

    def test_setting_attributes(self):
        func = lambda: print(1)

        runner = Runner(
            collection={
                'dir1': {
                    'do': func,
                    'directory_expansions': {'test': [1, 2, 3]}
                },
            }
        )

        expected = [
            Item(
                do=func,
                path_components=['dir1'],
                directory_expansions={'test': [1, 2, 3]}
            )
        ]

        expect(runner.items).to(equal(expected))

    def test_overwriting_attributes(self):
        func = lambda: print(1)

        runner = Runner(
            collection={
                'dir1': {
                    'directory_expansions': {'A': [1, 2, 3], 'B': [4, 5, 6]},
                    'prefix_expansions': {'Z': [1, 2]},
                    'subdir1': {
                        'do': func,
                        'directory_expansions': {'A': [7, 8, 9], 'C': [10, 11, 12]},
                    },
                },
            }
        )

        expected = [
            Item(
                do=func,
                path_components=['dir1', 'subdir1'],
                directory_expansions={'B': [4, 5, 6], 'A': [7, 8, 9], 'C': [10, 11, 12]},
                prefix_expansions={'Z': [1, 2]},
            )
        ]

        actual = runner.items

        expect(actual).to(equal(expected))

    def test_multiple_items(self):
        func1 = lambda: print(1)
        func2 = lambda: print(2)

        runner = Runner(
            collection={
                'dir1': {
                    'do': func1,
                },
                'dir2': {
                    'subdir2': func2,
                },
            }
        )

        expected = [
            Item(do=func1, path_components=['dir1']),
            Item(do=func2, path_components=['dir2', 'subdir2']),
        ]

        actual = runner.items

        expect(actual).to(equal(expected))

    def test_different_item_type(self):
        func1 = lambda: print(1)
        func2 = lambda: print(2)

        runner = Runner(
            collection={
                'one': {
                    'do': func1,
                    'expansion_type': PlotExpansion,
                },
                'two': func2,
            },
        )

        expected = [
            Item(do=func1, path_components=['one'], expansion_type=PlotExpansion),
            Item(do=func2, path_components=['two']),
        ]

        actual = runner.items

        expect(actual).to(equal(expected))


class TestItem:
    def test_sanitizes_function_arguments(self):
        def multiply(a, b, x=1, y=2):
            return x * y

        actual = Item(
            do=multiply,
            kwargs={'x': 1, 'z': 2},
            directory_expansions={'y': [1, 2, 3], 'w': [4, 5, 6]},
        )

        expected = Item(
            do=multiply,
            kwargs={'x': 1},
            directory_expansions={'y': [1, 2, 3]},
        )
       

        expect(actual).to(equal(expected))

    def test_filters_expansions(self):
        def multiply(a, b, x=1, y=2):
            return x * y

        actual = Item(
            do=multiply,
            kwargs={'x': 1},
            directory_expansions={'x': [1, 2, 3], 'y': [4, 5, 6]},
        )

        expected = Item(
            do=multiply,
            kwargs={'x': 1},
            directory_expansions={'x': [1], 'y': [4, 5, 6]},
        )

        expect(actual).to(equal(expected))

    def test_handles_list_args_in_expansions(self):
        def _zip(list1, list2):
            return list(zip(list1, list2))

        item = Item(
            do=_zip,
            kwargs={'list1': [1, 2]},
            suffix_expansions={'list2': [['a', 'b'], ['c', 'd']]},
            path_components = ['list-args-test'],
        )

        actual = [e.path for e in item.expansions]
        expected = [
            Item.CONFIG_DEFAULTS['results_dir'].joinpath('list-args-test-a+b.txt'),
            Item.CONFIG_DEFAULTS['results_dir'].joinpath('list-args-test-c+d.txt'),
        ]

        expect(actual).to(equal(expected))

    def test_handles_dict_args_in_expansions(self):
        def dict_multiply(dict1, dict2):
            return {k: v * dict2[k] for k, v in dict1.items()}

        item = Item(
            do=dict_multiply,
            kwargs={'dict1': {'a': 1, 'b': -1}},
            suffix_expansions={'dict2': [{'a': 2, 'b': 2}, {'a': 3, 'b': 3}]},
            path_components = ['dict-args-test'],
        )

        actual = [e.path for e in item.expansions]
        expected = [
            Item.CONFIG_DEFAULTS['results_dir'].joinpath('dict-args-test-a=2+b=2.txt'),
            Item.CONFIG_DEFAULTS['results_dir'].joinpath('dict-args-test-a=3+b=3.txt'),
        ]

        expect(actual).to(equal(expected))

    def test_defaults_to_first_arg(self):
        runner = Runner(
            collection={
                'directory_expansions': {'x': [1, 2, 3]},
                'a': lambda x: x,
            }
        )

        actual = runner.get_item('a').get_expansion().path
        expected = Item.CONFIG_DEFAULTS['results_dir'].joinpath('1', 'a.txt')

        expect(actual).to(equal(expected))

    def test_raises_exception_with_default(self):
        runner = Runner(
            collection={
                'directory_expansions': {'x': [1, 2, 3]},
                'arg_defaults': {
                    'x': 2,
                },
                'a': lambda x: x,
            }
        )

        actual = runner.get_item('a').get_expansion().path
        expected = Item.CONFIG_DEFAULTS['results_dir'].joinpath('2', 'a.txt')

        expect(actual).to(equal(expected))

    def test_converts_bools_to_strings(self):
        def fn(a=True, b=True):
            return {k: v * dict2[k] for k, v in dict1.items()}

        path_prefix = 'bool-args-test'
        item = Item(
            do=fn,
            suffix_expansions={'b': [False, True]},
            directory_expansions={'a': [False, True]},
            path_components = [path_prefix],
        )

        actual = [e.path for e in item.expansions]
        expected = [
            Item.CONFIG_DEFAULTS['results_dir'].joinpath('not-a', f'{path_prefix }-not-b.txt'),
            Item.CONFIG_DEFAULTS['results_dir'].joinpath('not-a', f'{path_prefix }-b.txt'),
            Item.CONFIG_DEFAULTS['results_dir'].joinpath('a', f'{path_prefix }-not-b.txt'),
            Item.CONFIG_DEFAULTS['results_dir'].joinpath('a', f'{path_prefix }-b.txt'),
        ]

        expect(actual).to(equal(expected))
