import functools
import itertools
import copy
import pandas as pd
import os

from pathlib import Path
import matplotlib.pyplot as plt


# TODO:
# 1. add a "suffix_expander" expander: takes a list of options, a key (to supply the
#    option on), and generates the expansions of the form `/name-{option}`
# 2. add a "nesting_expander" expander: takes a dictionary of lists of options,
#    key is kwargs key, list is values to expand

class AmbiguousCollectionQuery(Exception):
    pass


class Runner(object):
    def __init__(self, collection={}, directory=Path.cwd().joinpath('results')):
        """
        A collection is a dictionary of the form:
        {
            'some_string': function,
            ...
            'some_string': {
                'do': function,
                'kwargs': {kwargs for function},
                'no_plot': True if a matplotlib plot is not to be saved, False otherwise,
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
        """
        self.directory = directory
        self.collection = self.recursive_flatten_collection(collection)
        self.aliases = self.get_aliases(self.collection)

    @staticmethod
    def recursive_flatten_collection(collection):
        flat_collection = {}
        for item, val in collection.items():
            if callable(val):
                val = {'do': val}

            if 'do' in val:
                flat_collection[item] = val
            else:
                sub_items = Runner.recursive_flatten_collection(val)
                flat_collection.update({f"{item}/{key}": subval for key, subval in sub_items.items()})

        return flat_collection

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
        if not run_expansions:
            to_run = to_run[:1]

        figures_path = self.directory.joinpath('figures')

        for item_name, item_kwargs in to_run:
            path = Path(*item.get('subdirs', [])).joinpath(item_parent).joinpath(item_name)

            result = item['do'](**item_kwargs)

            if not item.get('no_plot'):
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

    def clean():
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
            for path in starting_directory.glob('**/*'):
                stemless_path = path.parent.joinpath(path.stem)

                if stemless_path not in collection_paths:
                    if not path.is_dir():
                        path.unlink()

                    parent = path.parent
                    if parent.is_dir() and not len(list(parent.glob('*'))):
                        parent.rmdir()
