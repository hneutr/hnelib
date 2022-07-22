from unittest.mock import patch
from pathlib import Path
from expects import *

from hnelib.new_runner import Runner, Item, PlotItem

class TestRunner:
    def test_parse_collection(self):
        func = lambda: print(1)

        runner = Runner(
            collection={
                'test': func
            }
        )

        expected = [Item(do=func, path_components=['test'])]

        expect(runner.collection).to(equal(expected))

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

        expect(runner.collection).to(equal(expected))

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

        expect(runner.collection).to(equal(expected))

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

        actual = runner.collection

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

        actual = runner.collection

        expect(actual).to(equal(expected))

    def test_different_item_type(self):
        func1 = lambda: print(1)
        func2 = lambda: print(2)

        runner = Runner(
            collection={'dir1': func1},
            default_item_type=PlotItem,
        )

        expected = [
            PlotItem(do=func1, path_components=['dir1']),
        ]

        actual = runner.collection

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
