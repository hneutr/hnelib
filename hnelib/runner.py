import functools
import itertools
import copy
import pandas as pd
import os
import inspect

from pathlib import Path
import matplotlib.pyplot as plt


# TODO:
# - allow for adding expansions at non-terminal nodes
#   - more broadly, allow for setting all flags at non-terminal nodes
# - allow for not writing the full terminal path if there is only one match
# for the path
# - allow specifying a path and running all objects underneath that path
# - remove `save_plots` argument and save plots only if a figure was generated
# - make `get_dataframe` run the item if the dataframe doesn't exist

class AmbiguousCollectionQuery(Exception):
    pass


class Runner(object):
    def __init__(
        self,
        collection={},
        directory=Path.cwd().joinpath('results'),
        save_plots=True,
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
                # flat_collection[item] = val
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
            (_args, _varargs, _kwargs, _, _, _, _)  = inspect.getfullargspec(do)

            # sanitize args if the function only has static arguments
            if _varargs == None and _kwargs == None:
                kwargs = {k: v for k, v in kwargs.items() if k in _args}

        if len(kwargs):
            val['kwargs'] = kwargs

        return val

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

        if len(path_matched_candidates) == 1:
            return path_matched_candidates[0]

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

    @property
    def figures_directory(self):
        path = self.directory.joinpath('figures')
        path.mkdir(exist_ok=True, parents=True)
        return path

    @property
    def dataframes_directory(self):
        path = self.directory.joinpath('dataframes')
        path.mkdir(exist_ok=True, parents=True)
        return path

    @property
    def tables_directory(self):
        return self.directory.joinpath('tables')

    def open_path(self, path):
        os.system(f'open "{str(path)}"')

    def open_figures(self):
        self.open_path(self.figures_directory)

    def open_dataframes(self):
        self.open_path(self.dataframes_directory)

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

    def get_figure_path(self, item_name_queried, item_kwargs={}, suffix='.png'):
        """
        returns the path to a figure
        """
        return self.get_qualified_path_for_result(
            result_path=self.get_result_path(item_name_queried, item_kwargs),
            directory=self.figures_directory,
            suffix=suffix,
        )

    def get_dataframe_path(self, item_name_queried, item_kwargs={}, suffix='.csv'):
        """
        returns the path to a dataframe
        """
        return self.get_qualified_path_for_result(
            result_path=self.get_result_path(item_name_queried, item_kwargs),
            directory=self.dataframes_directory,
            suffix=suffix,
        )

    def get_dataframe(self, *args, **kwargs):
        path = self.get_dataframe_path(*args, **kwargs)
        return pd.read_csv(path)

    @staticmethod
    def default_dataframe_formatter(df):
        return df.copy()

    def run_all(self, **kwargs):
        for item in self.collection:
            print(item)
            self.run(item, run_expansions=True, **kwargs)


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

            result = item['do'](**item_kwargs)

            if item.get('save_plot', True):
                self.save_plot(
                    path,
                    show=show,
                    directory=self.figures_directory,
                    **save_plot_kwargs,
                )

            if isinstance(result, pd.DataFrame) or item.get('save_df'):
                df = item.get('df_formatter', self.default_dataframe_formatter)(result)
                self.save_dataframe(
                    df,
                    path,
                    directory=self.dataframes_directory,
                    **save_dataframe_kwargs,
                )

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

    def save_plot(self, name, directory, show=False, suffix='.png', dpi=400):
        path = directory.joinpath(name).with_suffix(suffix)
        path.parent.mkdir(exist_ok=True, parents=True)
        path = str(path)

        plt.savefig(path, dpi=dpi, bbox_inches='tight')
        plt.clf()
        plt.close()

        if show:
            os.system(f'open "{path}"')

    def save_dataframe(self, df, name, directory, suffix=".csv"):
        path = directory.joinpath(name).with_suffix(suffix)
        path.parent.mkdir(exist_ok=True, parents=True)
        df.to_csv(path, index=False)

    def clean(self):
        """
        removes files in the base directories that are not part of the
        collection.
        """
        collection_paths = set()

        bases = [self.figures_directory, self.dataframes_directory]

        for name, item in self.collection.items():
            expansions = item.get('expander', self.default_expander)(
                name,
                item.get('kwargs', {}),
            )

            for name, _ in expansions:
                path = Path(*item.get('subdirs', [])).joinpath(name)

                for base in bases:
                    collection_paths.add(base.joinpath(path))

        for base in bases:
            for path in self.directory.glob('**/*'):
                stemless_path = path.parent.joinpath(path.stem)

                if stemless_path not in collection_paths:
                    if not path.is_dir():
                        path.unlink()

                    parent = path.parent
                    if parent.is_dir() and not len(list(parent.glob('*'))):
                        parent.rmdir()
