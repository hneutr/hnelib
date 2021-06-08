import pytest
from expects import *

from hnelib.runner import Runner

class TestRunner:
    runner =  Runner({
        'test': {
            'subtest': {
                'do': 1,
                'alias': 'alias-of-test',
            },
        },
        'top-test': {
            'do': 2,
        },
    })

    def test_flatten_collection_bare_function(self):
        func = lambda: print(1)
        collection = {
            'test': func
        }

        
        expected = {
            'test': {
                'do': func
            }
        }

        expect(Runner(collection).collection).to(equal(expected))

    def test_flatten_collection_no_nesting(self):
        collection = {
            'test': {
                'do': 1
            },
            'test2': {
                'do': 2
            },
        }

        expect(Runner(collection).collection).to(equal(collection))

    def test_flatten_collection_nesting(self):
        runner = Runner({
            'test': {
                'subtest': {
                    'do': 1
                },
                'subtest2': {
                    'do': 2
                },
            },
        })

        expect(runner.collection).to(equal({
            'test/subtest': {
                'do': 1
            },
            'test/subtest2': {
                'do': 2
            },
        }))

    def test_recursive_parents_match_no_candidates(self):
        actual = Runner.recursive_path_parents_match(
            ["1", "2"],
            []
        )
        expect(actual).to(equal(True))

    def test_recursive_parents_match_mismatch(self):
        actual = Runner.recursive_path_parents_match(
            ["1", "2"],
            ["3"],
        )
        expect(actual).to(equal(False))

    def test_recursive_parents_match_partial_match(self):
        actual = Runner.recursive_path_parents_match(
            ["1", "2"],
            ["2"],
        )
        expect(actual).to(equal(True))

    def test_recursive_parents_match_partial_match_mismatch(self):
        actual = Runner.recursive_path_parents_match(
            ["1", "2"],
            ["2", "3"],
        )
        expect(actual).to(equal(False))

    def test_find_item_exact_match(self):
        actual = self.runner.get_item('top-test')

        expect(actual).to(equal('top-test'))

    def test_find_item_nested_exact_match(self):
        actual = self.runner.get_item('test/subtest')

        expect(actual).to(equal('test/subtest'))

    def test_find_item_alias_match(self):
        actual = self.runner.get_item('alias-of-test')

        expect(actual).to(equal('test/subtest'))

    def test_find_item_stem_exact_match(self):
        actual = self.runner.get_item('subtest')

        expect(actual).to(equal('test/subtest'))

    def test_find_item_half_match(self):
        actual = self.runner.get_item('t/subtest')

        expect(actual).to(equal('test/subtest'))
