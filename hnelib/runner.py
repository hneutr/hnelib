from pathlib import Path
import copy
import inspect
import itertools
import json
import matplotlib.pyplot as plt
import os
import pandas as pd


# TODO:
# - allow for adding expansions at non-terminal nodes
#   - method: add `expand_over` key, which is a dict with values:
#       - values: prefixes, suffixes, directories
#       - treat them just like kwargs
# - allow for not writing the full terminal path if there is only one match
# for the path
# - allow specifying a path and running all objects underneath that path
# - remove `save_plots` argument and save plots only if a figure was generated
# - make `get_dataframe` run the item if the dataframe doesn't exist
# - support saving of json

class AmbiguousCollectionQuery(Exception):
    pass


class ItemNotFound(Exception):
    pass


class Runner(object):
    DEFAULTS = {
        'df_suffix': '.gz',
        'figure_suffix': '.png',
    }

    def __init__(
        self,
        collection={},
        directory=Path.cwd().joinpath('results'),
        save_plots=True,
        df_suffix=None,
        figure_suffix=None,
    ):
        """
        - collection: a dictionary of the form:
            {
                'some_string': function,
                ...
                'some_string': {
                    'do': function,
                    'kwargs': {kwargs for function},
                    'save_plot': Default: True. True if a matplotlib plot is not
                        to be saved, False otherwise,
                    'subdirs': [list, of, subdirectories, to, preappend, to, name],
                    'expander': function to expand the name, # TODO: more on this
                    'alias': shortform_name_of_function,
                },
                'directory': {
                    'subdirectory': {
                        'some_string1': ...,
                        'some_string2': ...,
                    }
                }
            }
            directories can be arbitrarily nested. Anything that has the 'do'
            keyword in it is an "item" to run later.
        - directory: Path. Default: `current working directory`/results. Where
            results will be saved.
        - save_plots: Bool. Default: True. Will expect items in the collection
            to result in matplotlib figures and save them after running `do`. If
            false, will not save them after running `do`.
        """
        self.directory = directory
        self.collection = self.recursive_flatten_collection(collection)
        self.aliases = self.get_aliases(self.collection)

        self.df_suffix = df_suffix if df_suffix else self.DEFAULTS['df_suffix']
        self.figure_suffix = figure_suffix if figure_suffix else self.DEFAULTS['figure_suffix']

    @classmethod
    def recursive_flatten_collection(cls, collection):
        """
        takes a nested dictionary like:
        {
            'directory': {
                'item_1': {
                    'do': function_1,
                },
                'item_2': {
                    'do': function_2,
                },
            },
        }

        and turns it into a flat dictionary like:
        {
            'directory/item_1': {
                'do': function_1,
            },
            'directory/item_2': {
                'do': function_2,
            },
        }

        if there are kwargs applied at the containing layers, they will be
        applied to the inner ones
        """
        flat_collection = {}

        kwargs = collection.pop('kwargs', {})

        for item, val in collection.items():
            if callable(val):
                val = {'do': val}

            val['kwargs'] = {
                **kwargs,
                **val.get('kwargs', {})
            }

            if 'do' in val:
                flat_collection[item] = cls.sanitize_kwargs_for_do_function(val)
            else:
                sub_items = Runner.recursive_flatten_collection(val)
                flat_collection.update({f"{item}/{key}": subval for key, subval in sub_items.items()})

        return flat_collection

    @classmethod
    def sanitize_kwargs_for_do_function(cls, val):
        """
        removes kwargs that will cause an error of the function
        """
        kwargs = val.pop('kwargs', {})

        do = val['do']

        if callable(do):
            kwargs = cls.sanitize_function_kwargs(do, kwargs)

        if len(kwargs):
            val['kwargs'] = kwargs

        return val

    @classmethod
    def sanitize_function_kwargs(cls, function, function_kwargs):
        (_args, _varargs, _kwargs, _, _, _, _) = inspect.getfullargspec(function)

        # sanitize args if the function only has static arguments
        if _varargs is None and _kwargs is None:
            function_kwargs = {k: v for k, v in function_kwargs.items() if k in _args}

        return function_kwargs

    def get_aliases(self, collection):
        aliases = {}
        for key, val in collection.items():
            if 'alias' in val:
                aliases[val['alias']] = key

        return aliases

    def get_item(self, string):
        """
        we want to be as generous as possible when responding to names, because
        sometimes we won't always want to fully specify a name.

        any time we can get a single match, we should return that match.

        Let's always assume that the last part is the "stem" (in pathlib terminology).

        I could see calling this in multiple ways:
        1. /[first letter of first dir]/[second letter of second dir]/name
        """
        if string in self.collection:
            # if we find an exact match, use it
            return string
        elif string in self.aliases:
            # if we find an exact alias match, use it
            return self.aliases[string]

        *string_parents, string_stem = string.split('/')

        candidates = {}
        for candidate in self.collection:
            *candidate_parents, candidate_stem = candidate.split('/')

            if candidate_stem == string_stem:
                # if we get a search string with 3 path segments
                # ('/1/2/3/stem'), then we can reject candidates with fewer than
                # 3 path segments ('/1/2/stem')
                if len(string_parents) <= len(candidate_parents):
                    candidates[candidate] = candidate_parents

        # If we find only one "stem" match, that's our match
        if len(candidates) == 1:
            return list(candidates.keys())[0]

        # if we have more than one "stem" match, try to use the pre-stem parts
        # to find a single match.
        #
        # We're going to be greedy here and try to 'startswith' match these
        # strings.
        #
        # we don't require things to be consecutive
        path_matched_candidates = []
        for candidate, candidate_parents in candidates.items():
            if self.recursive_path_parents_match(string_parents, candidate_parents):
                path_matched_candidates.append(candidate)

        if not path_matched_candidates:
            raise ItemNotFound
        elif len(path_matched_candidates) == 1:
            return path_matched_candidates[0]
        else:
            print('could not choose between:')
            for candidate in sorted(path_matched_candidates):
                print(f"\t{candidate}")

            raise AmbiguousCollectionQuery

    @staticmethod
    def recursive_path_parents_match(parents, candidate_parents):
        if not candidate_parents:
            return True

        for i, parent in enumerate(parents):
            if candidate_parents[0].startswith(parent):
                return Runner.recursive_path_parents_match(parents[i + 1:], candidate_parents[1:])

        return False

    def open_path(self, path):
        os.system(f'open "{str(path)}"')

    @staticmethod
    def default_expander(name, kwargs={}):
        """
        the default expander doesn't do anything, but in general, an expander
        takes a (name, kwargs) tuple and generates expansions from it.
        """
        return [(name, kwargs)]

    @staticmethod
    def get_expander(prefixes={}, suffixes={}, directories={}):
        """
        TODO:
        - change `name_options` to `suffixes`
        - add `prefixes`
        - change `directory_options` to `directories`


        name_options: a dictionary of lists. These will be appended to the name of the plot
            - keys: arguments to the function
            - values: a list of arguments to expand
        directory_options: a dictionary of lists. These will be turned into
        directories to put the plot in
            - keys: arguments to the function
            - values: a list of arguments to expand
        """
        prefix_keys = list(prefixes.keys())
        suffix_keys = list(suffixes.keys())
        directory_keys = list(directories.keys())

        all_options = {
            **prefixes,
            **suffixes,
            **directories,
        }

        def expander(name, kwargs={}):
            expansions = []
            for option_set in itertools.product(*list(all_options.values())):
                expansion_kwargs = copy.deepcopy(kwargs)

                index = 0

                prefix_kwargs = {k: option_set[index + i] for i, k in enumerate(prefix_keys)}
                index += len(prefixes)

                suffix_kwargs = {k: option_set[index + i] for i, k in enumerate(suffix_keys)}
                index += len(suffixes)

                directory_kwargs = {k: option_set[index + i] for i, k in enumerate(directory_keys)}

                expansion_kwargs.update(prefix_kwargs)
                expansion_kwargs.update(suffix_kwargs)
                expansion_kwargs.update(directory_kwargs)

                # Here's where we filter to the requested kwargs and don't
                # generate expansions that contradict the supplied kwargs
                if any([v for k, v in expansion_kwargs.items() if k in kwargs and kwargs[k] != v]):
                    continue

                stem_components = list(prefix_kwargs.values()) + [name] + list(suffix_kwargs.values())
                stem = "-".join([str(c) for c in stem_components])

                directories = [str(d) for d in list(directory_kwargs.values())]

                expansion_name = Path(*directories).joinpath(stem)

                expansions.append((expansion_name, expansion_kwargs))

            return expansions

        return expander

    def get_result_path(self, item_name_queried, item_kwargs={}):
        """
        This function returns a path for a given item query and kwargs combination.

        The kwargs should fully specify any parameters that are later expanded.

        The idea here is to be able to reference output locations without
        computing things. E.g., loading dataframes saved via plotters.
        """
        item_name = self.get_item(item_name_queried)
        item = self.collection[item_name]
        item_kwargs = {
            **item.get('kwargs', {}),
            **item_kwargs,
        }

        item_path = Path(item_name)
        item_parent = item_path.parent
        item_stem = item_path.stem

        to_run = item.get('expander', self.default_expander)(item_stem, item_kwargs)

        if len(to_run) > 1:
            raise AmbiguousCollectionQuery

        expanded_item_name, _ = to_run[0]

        path = Path(*item.get('subdirs', [])).joinpath(item_parent).joinpath(expanded_item_name)
        return path

    def get_qualified_path_for_result(self, result_path, directory, suffix):
        return directory.joinpath(result_path.parent, result_path.name + suffix)

    def get_figure_path(self, item_name_queried, item_kwargs={}, suffix=None):
        """
        returns the path to a figure
        """
        return self.get_qualified_path_for_result(
            result_path=self.get_result_path(item_name_queried, item_kwargs),
            directory=self.directory,
            suffix=suffix if suffix else self.figure_suffix,
        )

    def get_dataframe_path(self, item_name_queried, item_kwargs={}, suffix=None):
        """
        returns the path to a dataframe
        """
        return self.get_qualified_path_for_result(
            result_path=self.get_result_path(item_name_queried, item_kwargs),
            directory=self.directory,
            suffix=suffix if suffix else self.df_suffix,
        )

    def get_dataframe(self, *args, **kwargs):
        path = self.get_dataframe_path(*args, **kwargs)

        if not path.exists():
            item_name, to_run = self.get_items_to_run(*args, **kwargs)
            print(f"running: {item_name}")
            self.run(*args, **kwargs)

        return pd.read_csv(path)

    def get_df(self, *args, **kwargs):
        return self.get_dataframe(*args, **kwargs)

    def get_json_path(self, item_name_queried, item_kwargs={}):
        """
        returns the path to a json file
        """
        return self.get_qualified_path_for_result(
            result_path=self.get_result_path(item_name_queried, item_kwargs),
            directory=self.directory,
            suffix='.json',
        )

    def get_json(self, *args, **kwargs):
        path = self.get_json_path(*args, **kwargs)

        if not path.exists():
            item_name, to_run = self.get_items_to_run(*args, **kwargs)
            print(f"running: {item_name}")
            self.run(*args, **kwargs)

        return json.loads(path.read_text())

    @staticmethod
    def default_dataframe_formatter(df):
        return df.copy()

    def run_all(self, **kwargs):
        for item in self.collection:
            print(item)
            self.run(item, run_expansions=True, **kwargs)

    def run_subcollection(self, query_string, run_expansions=True, **kwargs):
        """
        """
        item_names = [c for c in self.collection if c.startswith(query_string)]
        for item_name in item_names:
            print(item_name)
            self.run(item_name_queried=item_name, run_expansions=run_expansions, **kwargs)

    def run(
        self,
        item_name_queried,
        show=False,
        item_kwargs={},
        run_expansions=False,
        save_plot_kwargs={},
        save_dataframe_kwargs={},
    ):
        item_name, to_run = self.get_items_to_run(item_name_queried, item_kwargs, run_expansions)

        item = self.collection[item_name]
        item_parent = Path(item_name).parent

        for item_name, item_kwargs in to_run:
            path = Path(*item.get('subdirs', [])).joinpath(item_parent).joinpath(item_name)

            item_kwargs = self.sanitize_function_kwargs(item['do'], item_kwargs)

            result = item['do'](**item_kwargs)

            if item.get('save_plot', True):
                self.save_plot(
                    path,
                    show=show,
                    directory=self.directory,
                    **save_plot_kwargs,
                )

            if isinstance(result, pd.DataFrame) or item.get('save_df'):
                df = item.get('df_formatter', self.default_dataframe_formatter)(result)
                self.save_dataframe(
                    df,
                    path,
                    directory=self.directory,
                    **save_dataframe_kwargs,
                )
            elif result != None:
                try:
                    self.save_json(
                        result,
                        path,
                        directory=self.directory,
                    )
                except TypeError:
                    pass

    def get_items_to_run(
        self,
        item_name_queried,
        item_kwargs={},
        run_expansions=False,
    ):
        item_name = self.get_item(item_name_queried)
        item = self.collection[item_name]
        item_kwargs = {
            **item.get('kwargs', {}),
            **item_kwargs,
        }

        item_path = Path(item_name)

        to_run = item.get('expander', self.default_expander)(item_path.stem, item_kwargs)
        if not run_expansions:
            to_run = to_run[:1]

        return item_name, to_run

    def save_plot(self, name, directory, show=False, suffix=None, dpi=400):
        path = directory.joinpath(name).with_suffix(suffix if suffix else self.figure_suffix)
        path.parent.mkdir(exist_ok=True, parents=True)
        path = str(path)

        plt.savefig(path, dpi=dpi, bbox_inches='tight')
        plt.clf()
        plt.close()

        if show:
            os.system(f'open "{path}"')

    def save_dataframe(self, df, name, directory, suffix=None):
        path = directory.joinpath(name).with_suffix(suffix if suffix else self.df_suffix)
        path.parent.mkdir(exist_ok=True, parents=True)
        df.to_csv(path, index=False)

    def save_json(self, thing, name, directory):
        path = directory.joinpath(name).with_suffix('.json')
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(json.dumps(thing, indent=4, sort_keys=True))

    def clean(self):
        """
        removes files in the base directories that are not part of the
        collection.
        """
        collection_paths = set()

        for name, item in self.collection.items():
            expansions = item.get('expander', self.default_expander)(
                name,
                item.get('kwargs', {}),
            )

            print("I think we're not actually getting the expansions...")

            for name, _ in expansions:
                path = Path(*item.get('subdirs', [])).joinpath(name)

                collection_paths.add(self.directory.joinpath(path))

        to_remove = []
        for path in self.directory.rglob('*'):
            stemless_path = path.parent.joinpath(path.stem)

            if stemless_path not in collection_paths:
                to_remove.append(path)

        for path in to_remove:
            if not path.exists():
                continue

            if not path.is_dir():
                path.unlink()

            parent = path.parent
            if parent.is_dir() and not len(list(parent.glob('*'))):
                parent.rmdir()
