from unittest.mock import patch
from pathlib import Path
from expects import *

from hnelib.new_runner import Runner, Item

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

    def test_over(self):
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
