from unittest.mock import patch
from pathlib import Path
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

    def test_weird_case(self):
        collection = {
            "questions/1-winners-and-losers/1-demographics/across-demographics": lambda: 1,
            "questions/2-who-competes-with-whom/3-by-stiffness/across-demographics": lambda: 2,
        }

        runner = Runner(collection)

        expect(runner.get_item('q/1/1/across-demographics')).to(equal(
            'questions/1-winners-and-losers/1-demographics/across-demographics'
        ))

    def test_expander_prefix(self):
        expander = Runner.get_expander(prefixes={'test_kwarg': [1, 2]})

        expected = [
            (Path('1-test'), {'test_kwarg': 1}),
            (Path('2-test'), {'test_kwarg': 2}),
        ]

        expect(expander('test')).to(equal(expected))

    def test_expander_prefix_with_kwargs(self):
        expander = Runner.get_expander(prefixes={'test_kwarg': [1, 2]})

        expected = [
            (Path('2-test'), {'test_kwarg': 2}),
        ]

        expect(expander('test', kwargs={'test_kwarg': 2})).to(equal(expected))

    def test_expander_multiple_prefixes(self):
        expander = Runner.get_expander(
            prefixes={
                'test_kwarg1': [1, 2],
                'test_kwarg2': [3, 4],
            }
        )

        expected = [
            (Path('1-3-test'), {'test_kwarg1': 1, 'test_kwarg2': 3}),
            (Path('1-4-test'), {'test_kwarg1': 1, 'test_kwarg2': 4}),
            (Path('2-3-test'), {'test_kwarg1': 2, 'test_kwarg2': 3}),
            (Path('2-4-test'), {'test_kwarg1': 2, 'test_kwarg2': 4}),
        ]

        expect(expander('test')).to(equal(expected))

    def test_expander_directory(self):
        expander = Runner.get_expander(
            directories={
                'directory': [1, 2],
            },
        )

        expected = [
            (Path('1', 'test'), {'directory': 1}),
            (Path('2', 'test'), {'directory': 2}),
        ]

        expect(expander('test')).to(equal(expected))

    def test_expander_suffix(self):
        expander = Runner.get_expander(
            suffixes={
                'suffix': [1, 2],
            },
        )

        expected = [
            (Path('test-1'), {'suffix': 1}),
            (Path('test-2'), {'suffix': 2}),
        ]

        expect(expander('test')).to(equal(expected))

    def test_expander_prefix_suffix_directory(self):
        expander = Runner.get_expander(
            prefixes={
                'prefix': [1, 2],
            },
            suffixes={
                'suffix': [3, 4],
            },
            directories={
                'directory': [5, 6],
            },
        )

        expected = [
            (Path('5', '1-test-3'), {'prefix': 1, 'suffix': 3, 'directory': 5}),
            (Path('6', '1-test-3'), {'prefix': 1, 'suffix': 3, 'directory': 6}),
            (Path('5', '1-test-4'), {'prefix': 1, 'suffix': 4, 'directory': 5}),
            (Path('6', '1-test-4'), {'prefix': 1, 'suffix': 4, 'directory': 6}),
            (Path('5', '2-test-3'), {'prefix': 2, 'suffix': 3, 'directory': 5}),
            (Path('6', '2-test-3'), {'prefix': 2, 'suffix': 3, 'directory': 6}),
            (Path('5', '2-test-4'), {'prefix': 2, 'suffix': 4, 'directory': 5}),
            (Path('6', '2-test-4'), {'prefix': 2, 'suffix': 4, 'directory': 6}),
        ]

        expect(expander('test')).to(equal(expected))

    def test_get_result_path(self):
        runner =  Runner({
            'test': {
                'subtest': {
                    'do': 1,
                    'expander': Runner.get_expander(
                        directories={'dir': [1, 2]},
                        prefixes={'pre': [3, 4]},
                        suffixes={'post': [5, 6]},
                    ),
                },
            },
        })

        expected = Path('test', '2', '4-subtest-6')
        actual = runner.get_result_path('test/subtest', {'dir': 2, 'pre': 4, 'post': 6})

        expect(actual).to(equal(expected))

    def test_get_dataframe_path(self):
        runner =  Runner({
            'test': {
                'subtest': {
                    'do': 1,
                    'expander': Runner.get_expander(
                        directories={'dir': [1, 2]},
                        prefixes={'pre': [3, 4]},
                        suffixes={'post': [5, 6]},
                    ),
                },
            },
        })

        expected = Path.cwd().joinpath('results', 'test', '2', '4-subtest-6.gz')
        actual = runner.get_dataframe_path('test/subtest', {'dir': 2, 'pre': 4, 'post': 6})

        expect(actual).to(equal(expected))

    def test_inherited_parameters_are_applied(self):
        """
        test that parameter defaults set at a non-leaf node are propogated down
        """
        runner =  Runner({
            'test': {
                'subtest': {
                    'do': 1,
                    'kwargs': {
                        'param_one': 1
                    },
                },
                'sub': {
                    'subsubtest': {
                        'do': 2,
                        'kwargs': {
                            'param_one': 2
                        },
                    },
                },
                'kwargs': {
                    'param_two': 3,
                },
            },
        })

        expected = {
            'test/subtest': {
                'do': 1,
                'kwargs': {
                    'param_two': 3,
                    'param_one': 1,
                },
            },
            'test/sub/subsubtest': {
                'do': 2,
                'kwargs': {
                    'param_two': 3,
                    'param_one': 2,
                },
            },
        }

        expect(runner.collection).to(equal(expected))

    def test_inherited_parameter_can_be_overridden(self):
        """
        test that parameter defaults set at a non-leaf node can be overwritten by children
        """
        runner =  Runner({
            'test': {
                'subtest': {
                    'do': 1,
                    'kwargs': {
                        'param_two': 1
                    },
                },
                'kwargs': {
                    'param_two': 3,
                },
            },
        })

        expected = {
            'test/subtest': {
                'do': 1,
                'kwargs': {
                    'param_two': 1,
                },
            },
        }

        expect(runner.collection).to(equal(expected))

    def test_parameters_are_not_applied_to_functions_that_do_not_take_them(self):
        """
        test that parameters are not applied to functions that cannot accept them
        """
        def test_function(param_one, param_two):
            pass

        runner =  Runner({
            'test': {
                'subtest': {
                    'do': test_function,
                    'kwargs': {
                        'param_one': 1
                    },
                },
                'kwargs': {
                    'param_three': 3,
                },
            },
        })

        expected = {
            'test/subtest': {
                'do': test_function,
                'kwargs': {
                    'param_one': 1,
                },
            },
        }

        expect(runner.collection).to(equal(expected))

    def test_inherited_are_applied_to_functions_with_kwargs(self):
        def test_function(param_one, param_two, **kwargs):
            pass

        runner = Runner({
            'test': {
                'subtest': {
                    'do': test_function,
                    'kwargs': {
                        'param_one': 1
                    },
                },
                'kwargs': {
                    'param_three': 3,
                },
            },
        })

        expected = {
            'test/subtest': {
                'do': test_function,
                'kwargs': {
                    'param_one': 1,
                    'param_three': 3,
                },
            },
        }

        expect(runner.collection).to(equal(expected))

    # @pytest.mark.focus
    def test_run_subcollection_matches(self):
        actual = []
        def test_function_to_run():
            actual.append(1)

        def test_function_not_to_be_run():
            actual.append(2)

        runner = Runner({
            'test': {
                'subtest': {
                    'test1': test_function_to_run,
                    'test2': test_function_to_run,
                },
                'not-subtest': test_function_not_to_be_run,
            },
        })

        expected = [1, 1]

        runner.run_subcollection('test/subtest')
        expect(actual).to(equal(expected))
