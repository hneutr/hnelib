from pathlib import Path
from collections import defaultdict
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
# - allow for not writing the full terminal path if there is only one match for
# the path
# - remove `save_plots` argument and save plots only if a figure was generated
# - add a `rerun` flag to `get_dataframe` 
#   - have option to rerun:
#       - shallowly: just the item called
#       - deeply: rerun everything it calls

class AmbiguousCollectionQuery(Exception):
    pass


class ItemNotFound(Exception):
    pass


class Instance(object):
    """
    an Instance is an instantiation of an Item — basically, a single expansion
    """
    def __init__(self, item, **kwargs):
        self.item = item
        self.kwargs = self.sanitize_kwargs(kwargs)

    @property
    def path(self):
        1

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

    # @classmethod
    # def sanitize_function_kwargs(cls, function, function_kwargs):
    #     (_args, _varargs, _kwargs, _, _, _, _) = inspect.getfullargspec(function)

    #     # sanitize args if the function only has static arguments
    #     if _varargs is None and _kwargs is None:
    #         function_kwargs = {k: v for k, v in function_kwargs.items() if k in _args}

    #     return function_kwargs

    @property
    def run(self):
        1


class Item(object):
    """
    an item is an element in a collection that gets fed to a Runner.

    it defines:
    - what an element in a collection looks like: the set of keys it supports
    - what to do with a result
    - how to save it
    """
    SUFFIXES = ['.txt']

    CONFIG_DEFAULTS = {
        'path_components': [],
        'kwargs': {},
        'expand_over': {
            'directories': {},
            'prefixes': {},
            'suffixes': {},
        },
        'item_type': None,
    }

    LEAF_CONFIG_DEFAULTS = {
        'do': lambda: None,
        'subdirs': [],
        'aliases': [],
    }

    ALL_CONFIG_DEFAULTS = {**CONFIG_DEFAULTS, **LEAF_CONFIG_DEFAULTS}

    def __init__(self, **kwargs):
        for key, val in self.ALL_CONFIG_DEFAULTS.items():
            if key == 'expand_over':
                kwargs[key] = self.merge_expand_over_content(val, kwargs.get(key, {}))

            setattr(self, key, kwargs.get(key, val))

    def __eq__(self, other):
        conditions = []
        for key in self.ALL_CONFIG_DEFAULTS:
            conditions.append(getattr(self, key) == getattr(other, key))

        return all(conditions)


    @classmethod
    def is_item(cls, config):
        return 'do' in config

    @staticmethod
    def format_collection(collection):
        if callable(collection):
            collection = {
                'do': collection
            }

        return collection

    @classmethod
    def update_config(cls, config, collection, path=''):
        """
        take the config from the parent
        - remove all non-CONFIG_DEFAULTS content from config
        - add `path` to config['path']
        - use data in `collection` to update:
            - config['kwargs']
            - config['expand_over']
            - config['item_type']
            - all `LEAF_CONFIG_DEFAULTS`
        """
        config = cls.sanitize_parent_config(config)

        if path:
            config['path_components'].append(path)

        config['item_type'] = collection.get('item_type', config.get('item_type'))

        config['kwargs'].update(collection.get('kwargs', {}))

        config['expand_over'] = cls.merge_expand_over_content(
            config.get('expand_over', {}),
            collection.get('expand_over', {}),
        )

        config.update({k: v for k, v in collection.items() if k in config['item_type'].LEAF_CONFIG_DEFAULTS})

        return config

    @classmethod
    def sanitize_parent_config(cls, config):
        """
        a parent config should have only Item.CONFIG_DEFAULTS keys
        """
        new_config = {}
        for key, default in cls.CONFIG_DEFAULTS.items():
            if key == 'expand_over':
                new_config[key] = cls.merge_expand_over_content(default, config.get(key, {}))
            else:
                new_config[key] = config.get(key, default)

        return new_config

    @classmethod
    def merge_expand_over_content(cls, old, new):
        merged = cls.CONFIG_DEFAULTS['expand_over']

        for key in merged:
            for e in [old, new]:
                merged[key].update(e.get(key, {}))

        return merged

    @classmethod
    def from_config(cls, config):
        item_type = config.pop('item_type')
        return item_type(**config)

    @property
    def path(self):
        1

    @property
    def save(self):
        1

    @property
    def expansions(self):
        1

    @property
    def collections(self):
        1

    def matches_query(self, query):
        1

    def matches_collection_query(self, query):
        1

    def get_instance(**kwargs):
        1


class PlotItem(Item):
    SUFFIXES = ['.png', '.pdf']


class DataFrameItem(Item):
    SUFFIXES = ['.gz', '.csv']

    LEAF_CONFIG_DEFAULTS = {
        **Item.LEAF_CONFIG_DEFAULTS,
        'formatter': lambda df: df.copy(),
    }

    ALL_CONFIG_DEFAULTS = {**Item.CONFIG_DEFAULTS, **LEAF_CONFIG_DEFAULTS}


class JSONItem(Item):
    SUFFIXES = ['.json']


class Runner(object):
    ITEM_TYPES = [
        PlotItem,
        DataFrameItem,
        JSONItem,
    ]

    def __init__(
        self,
        collection={},
        directory=Path.cwd().joinpath('results'),
        default_item_type=Item,
    ):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True, parents=True)

        self.default_item_type = default_item_type

        self.collection = self.parse_collection(
            collection=collection,
            parent_config={
                'path_components': [],
                'item_type': default_item_type,
            },
        )

    @classmethod
    def parse_collection(cls, collection, parent_config, path=''):
        collection = Item.format_collection(collection)

        config = Item.update_config(
            config=parent_config,
            collection=collection,
            path=path,
        )

        collection = {k: v for k, v in collection.items() if k not in config}

        items = []
        if Item.is_item(config):
            items.append(Item.from_config(config))
        else:
            for key, subcollection in collection.items():
                items += cls.parse_collection(
                    collection=subcollection,
                    parent_config=config,
                    path=key,
                )

        return items


    #@classmethod
    #def recursive_flatten_collection(cls, collection):
    #    """
    #    takes a nested dictionary like:
    #    {
    #        'directory': {
    #            'item_1': {
    #                'do': function_1,
    #            },
    #            'item_2': {
    #                'do': function_2,
    #            },
    #        },
    #    }

    #    and turns it into a flat dictionary like:
    #    {
    #        'directory/item_1': {
    #            'do': function_1,
    #        },
    #        'directory/item_2': {
    #            'do': function_2,
    #        },
    #    }

    #    if there are kwargs applied at the containing layers, they will be
    #    applied to the inner ones
    #    """
    #    flat_collection = {}

    #    kwargs = collection.pop('kwargs', {})

    #    for item, val in collection.items():
    #        if callable(val):
    #            val = {'do': val}

    #        val['kwargs'] = {
    #            **kwargs,
    #            **val.get('kwargs', {})
    #        }

    #        if 'do' in val:
    #            flat_collection[item] = cls.sanitize_kwargs_for_do_function(val)
    #        else:
    #            sub_items = Runner.recursive_flatten_collection(val)
    #            flat_collection.update({f"{item}/{key}": subval for key, subval in sub_items.items()})

    #    return flat_collection

    #@classmethod
    #def sanitize_kwargs_for_do_function(cls, val):
    #    """
    #    removes kwargs that will cause an error of the function
    #    """
    #    kwargs = val.pop('kwargs', {})

    #    do = val['do']

    #    if callable(do):
    #        kwargs = cls.sanitize_function_kwargs(do, kwargs)

    #    if len(kwargs):
    #        val['kwargs'] = kwargs

    #    return val

    #@classmethod
    #def sanitize_function_kwargs(cls, function, function_kwargs):
    #    (_args, _varargs, _kwargs, _, _, _, _) = inspect.getfullargspec(function)

    #    # sanitize args if the function only has static arguments
    #    if _varargs is None and _kwargs is None:
    #        function_kwargs = {k: v for k, v in function_kwargs.items() if k in _args}

    #    return function_kwargs

    #def get_aliases(self, collection):
    #    aliases = {}
    #    for key, val in collection.items():
    #        if 'alias' in val:
    #            aliases[val['alias']] = key

    #    return aliases

    #def get_item(self, string):
    #    """
    #    we want to be as generous as possible when responding to names, because
    #    sometimes we won't always want to fully specify a name.

    #    any time we can get a single match, we should return that match.

    #    Let's always assume that the last part is the "stem" (in pathlib terminology).

    #    I could see calling this in multiple ways:
    #    1. /[first letter of first dir]/[second letter of second dir]/name
    #    """
    #    if string in self.collection:
    #        # if we find an exact match, use it
    #        return string
    #    elif string in self.aliases:
    #        # if we find an exact alias match, use it
    #        return self.aliases[string]

    #    *string_parents, string_stem = string.split('/')

    #    candidates = {}
    #    for candidate in self.collection:
    #        *candidate_parents, candidate_stem = candidate.split('/')

    #        if candidate_stem == string_stem:
    #            # if we get a search string with 3 path segments
    #            # ('/1/2/3/stem'), then we can reject candidates with fewer than
    #            # 3 path segments ('/1/2/stem')
    #            if len(string_parents) <= len(candidate_parents):
    #                candidates[candidate] = candidate_parents

    #    # If we find only one "stem" match, that's our match
    #    if len(candidates) == 1:
    #        return list(candidates.keys())[0]

    #    # if we have more than one "stem" match, try to use the pre-stem parts
    #    # to find a single match.
    #    #
    #    # We're going to be greedy here and try to 'startswith' match these
    #    # strings.
    #    #
    #    # we don't require things to be consecutive
    #    path_matched_candidates = []
    #    for candidate, candidate_parents in candidates.items():
    #        if self.recursive_path_parents_match(string_parents, candidate_parents):
    #            path_matched_candidates.append(candidate)

    #    if not path_matched_candidates:
    #        raise ItemNotFound
    #    elif len(path_matched_candidates) == 1:
    #        return path_matched_candidates[0]
    #    else:
    #        print('could not choose between:')
    #        for candidate in sorted(path_matched_candidates):
    #            print(f"\t{candidate}")

    #        raise AmbiguousCollectionQuery

    #@staticmethod
    #def recursive_path_parents_match(parents, candidate_parents):
    #    if not candidate_parents:
    #        return True

    #    for i, parent in enumerate(parents):
    #        if candidate_parents[0].startswith(parent):
    #            return Runner.recursive_path_parents_match(parents[i + 1:], candidate_parents[1:])

    #    return False

    #################################################################################
    ##
    ##
    ## expanders
    ##
    ##
    #################################################################################
    #@staticmethod
    #def default_expander(name, kwargs={}):
    #    """
    #    the default expander doesn't do anything, but in general, an expander
    #    takes a (name, kwargs) tuple and generates expansions from it.
    #    """
    #    return [(name, kwargs)]

    #@staticmethod
    #def get_expander(prefixes={}, suffixes={}, directories={}):
    #    """
    #    TODO:
    #    - change `name_options` to `suffixes`
    #    - add `prefixes`
    #    - change `directory_options` to `directories`


    #    name_options: a dictionary of lists. These will be appended to the name of the plot
    #        - keys: arguments to the function
    #        - values: a list of arguments to expand
    #    directory_options: a dictionary of lists. These will be turned into
    #    directories to put the plot in
    #        - keys: arguments to the function
    #        - values: a list of arguments to expand
    #    """
    #    prefix_keys = list(prefixes.keys())
    #    suffix_keys = list(suffixes.keys())
    #    directory_keys = list(directories.keys())

    #    all_options = {
    #        **prefixes,
    #        **suffixes,
    #        **directories,
    #    }

    #    def expander(name, kwargs={}):
    #        expansions = []
    #        for option_set in itertools.product(*list(all_options.values())):
    #            expansion_kwargs = copy.deepcopy(kwargs)

    #            index = 0

    #            prefix_kwargs = {k: option_set[index + i] for i, k in enumerate(prefix_keys)}
    #            index += len(prefixes)

    #            suffix_kwargs = {k: option_set[index + i] for i, k in enumerate(suffix_keys)}
    #            index += len(suffixes)

    #            directory_kwargs = {k: option_set[index + i] for i, k in enumerate(directory_keys)}

    #            expansion_kwargs.update(prefix_kwargs)
    #            expansion_kwargs.update(suffix_kwargs)
    #            expansion_kwargs.update(directory_kwargs)

    #            # Here's where we filter to the requested kwargs and don't
    #            # generate expansions that contradict the supplied kwargs
    #            if any([v for k, v in expansion_kwargs.items() if k in kwargs and kwargs[k] != v]):
    #                continue

    #            stem_components = list(prefix_kwargs.values()) + [name] + list(suffix_kwargs.values())
    #            stem = "-".join([str(c) for c in stem_components])

    #            directories = [str(d) for d in list(directory_kwargs.values())]

    #            expansion_name = Path(*directories).joinpath(stem)

    #            expansions.append((expansion_name, expansion_kwargs))

    #        return expansions

    #    return expander

    #@staticmethod
    #def default_dataframe_formatter(df):
    #    return df.copy()

    #################################################################################
    ##
    ##
    ## item result access
    ##
    ##
    #################################################################################
    #def get_result_path(self, item_name_queried, item_kwargs={}):
    #    """
    #    This function returns a path for a given item query and kwargs combination.

    #    The kwargs should fully specify any parameters that are later expanded.

    #    The idea here is to be able to reference output locations without
    #    computing things. E.g., loading dataframes saved via plotters.
    #    """
    #    item_name = self.get_item(item_name_queried)
    #    item = self.collection[item_name]
    #    item_kwargs = {
    #        **item.get('kwargs', {}),
    #        **item_kwargs,
    #    }

    #    item_path = Path(item_name)
    #    item_parent = item_path.parent
    #    item_stem = item_path.stem

    #    to_run = item.get('expander', self.default_expander)(item_stem, item_kwargs)

    #    if len(to_run) > 1:
    #        raise AmbiguousCollectionQuery

    #    expanded_item_name, _ = to_run[0]

    #    path = Path(*item.get('subdirs', [])).joinpath(item_parent).joinpath(expanded_item_name)
    #    return path

    #def get_qualified_path_for_result(self, result_path, suffix):
    #    return self.directory.joinpath(result_path.parent, result_path.name + suffix)

    #def get_figure_path(self, item_name_queried, item_kwargs={}, suffix=None):
    #    return self.get_qualified_path_for_result(
    #        result_path=self.get_result_path(item_name_queried, item_kwargs),
    #        suffix=suffix if suffix else self.figure_suffix,
    #    )

    #def get_dataframe_path(self, item_name_queried, item_kwargs={}, suffix=None):
    #    return self.get_qualified_path_for_result(
    #        result_path=self.get_result_path(item_name_queried, item_kwargs),
    #        suffix=suffix if suffix else self.df_suffix,
    #    )

    #def get_json_path(self, item_name_queried, item_kwargs={}):
    #    return self.get_qualified_path_for_result(
    #        result_path=self.get_result_path(item_name_queried, item_kwargs),
    #        suffix='.json',
    #    )

    #def get_dataframe(self, *args, **kwargs):
    #    path = self.get_dataframe_path(*args, **kwargs)

    #    if not path.exists():
    #        item_name, to_run = self.get_items_to_run(*args, **kwargs)
    #        print(f"running: {item_name}")
    #        self.run(*args, **kwargs)

    #    return pd.read_csv(path)

    #def get_df(self, *args, **kwargs):
    #    return self.get_dataframe(*args, **kwargs)

    #def get_json(self, *args, **kwargs):
    #    path = self.get_json_path(*args, **kwargs)

    #    if not path.exists():
    #        item_name, to_run = self.get_items_to_run(*args, **kwargs)
    #        print(f"running: {item_name}")
    #        self.run(*args, **kwargs)

    #    return json.loads(path.read_text())

    #################################################################################
    ##
    ##
    ## running
    ##
    ##
    #################################################################################
    #def run_all(self, **kwargs):
    #    for item in self.collection:
    #        print(item)
    #        self.run(item, run_expansions=True, **kwargs)

    #def run_subcollection(self, query_string, run_expansions=True, **kwargs):
    #    """
    #    """
    #    item_names = [c for c in self.collection if c.startswith(query_string)]
    #    for item_name in item_names:
    #        print(item_name)
    #        self.run(item_name_queried=item_name, run_expansions=run_expansions, **kwargs)

    #def run(
    #    self,
    #    item_name_queried,
    #    show=False,
    #    item_kwargs={},
    #    run_expansions=False,
    #    save_plot_kwargs={},
    #    save_dataframe_kwargs={},
    #):
    #    item_name, to_run = self.get_items_to_run(item_name_queried, item_kwargs, run_expansions)

    #    item = self.collection[item_name]
    #    item_parent = Path(item_name).parent

    #    for item_name, item_kwargs in to_run:
    #        path = Path(*item.get('subdirs', [])).joinpath(item_parent).joinpath(item_name)

    #        item_kwargs = self.sanitize_function_kwargs(item['do'], item_kwargs)

    #        result = item['do'](**item_kwargs)

    #        if item.get('save_plot', True) and self.save_plots:
    #            self.save_plot(
    #                path,
    #                show=show,
    #                directory=self.directory,
    #                **save_plot_kwargs,
    #            )

    #        if isinstance(result, pd.DataFrame) or item.get('save_df'):
    #            df = item.get('df_formatter', self.default_dataframe_formatter)(result)

    #            self.save_dataframe(
    #                df,
    #                path,
    #                directory=self.directory,
    #                **save_dataframe_kwargs,
    #            )
    #        elif result != None:
    #            try:
    #                self.save_json(
    #                    result,
    #                    path,
    #                    directory=self.directory,
    #                )
    #            except TypeError:
    #                pass

    #def get_items_to_run(
    #    self,
    #    item_name_queried,
    #    item_kwargs={},
    #    run_expansions=False,
    #):
    #    item_name = self.get_item(item_name_queried)
    #    item = self.collection[item_name]
    #    item_kwargs = {
    #        **item.get('kwargs', {}),
    #        **item_kwargs,
    #    }

    #    item_path = Path(item_name)

    #    to_run = item.get('expander', self.default_expander)(item_path.stem, item_kwargs)
    #    if not run_expansions:
    #        to_run = to_run[:1]

    #    return item_name, to_run

    #################################################################################
    ##
    ##
    ## cleaning (I think this doesn't work right now)
    ##
    ##
    #################################################################################
    #def clean(self):
    #    """
    #    removes files in the base directories that are not part of the
    #    collection.
    #    """
    #    collection_paths = set()

    #    for name, item in self.collection.items():
    #        expansions = item.get('expander', self.default_expander)(
    #            name,
    #            item.get('kwargs', {}),
    #        )

    #        print("I think we're not actually getting the expansions...")

    #        for name, _ in expansions:
    #            path = Path(*item.get('subdirs', [])).joinpath(name)

    #            collection_paths.add(self.directory.joinpath(path))

    #    to_remove = []
    #    for path in self.directory.rglob('*'):
    #        stemless_path = path.parent.joinpath(path.stem)

    #        if stemless_path not in collection_paths:
    #            to_remove.append(path)

    #    for path in to_remove:
    #        if not path.exists():
    #            continue

    #        if not path.is_dir():
    #            path.unlink()

    #        parent = path.parent
    #        if parent.is_dir() and not len(list(parent.glob('*'))):
    #            parent.rmdir()

    #################################################################################
    ##
    ##
    ## saving
    ##
    ##
    #################################################################################
    #def save_plot(self, name, directory, show=False, suffix=None, dpi=400):
    #    path = directory.joinpath(name).with_suffix(suffix if suffix else self.figure_suffix)
    #    path.parent.mkdir(exist_ok=True, parents=True)
    #    path = str(path)

    #    plt.savefig(path, dpi=dpi, bbox_inches='tight')
    #    plt.clf()
    #    plt.close()

    #    if show:
    #        os.system(f'open "{path}"')

    #def save_dataframe(self, df, name, directory, suffix=None):
    #    path = directory.joinpath(name).with_suffix(suffix if suffix else self.df_suffix)
    #    path.parent.mkdir(exist_ok=True, parents=True)
    #    df.to_csv(path, index=False)

    #def save_json(self, thing, name, directory):
    #    path = directory.joinpath(name).with_suffix('.json')
    #    path.parent.mkdir(exist_ok=True, parents=True)
    #    path.write_text(json.dumps(thing, indent=4, sort_keys=True))

