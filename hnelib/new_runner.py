from pathlib import Path
from functools import cached_property
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


class Expansion(object):
    """
    an Expansion is an instantiation of an Item — basically, a single expansion
    """
    def __init__(self, item, kwargs):
        self.item = item
        self.kwargs = kwargs

    @cached_property
    def path(self):
        expansion_composition = self.item.get_expansion_composition(self.kwargs)

        stem_components = expansion_composition['prefixes']
        stem_components += [self.item.name]
        stem_components += expansion_composition['suffixes']

        stem = "-".join([str(s) for s in stem_components])

        directories = [str(d) for d in expansion_composition['directories']]
        directories += self.item.subdirs

        return Path(*directories).joinpath(stem)

    def save(self, result, directory, suffix=None, **kwargs):
        suffix = suffix if suffix else self.item.SUFFIXES[0]

        path = directory.joinpath(self.item.directory, self.path).with_suffix(suffix)
        path.parent.mkdir(exist_ok=True, parents=True)

        self.item.save(result, path, **kwargs)

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
        'directory_expansions': {},
        'prefix_expansions': {},
        'suffix_expansions': {},
        'item_type': None,
    }

    LEAF_CONFIG_DEFAULTS = {
        'do': lambda: None,
        'subdirs': [],
        'aliases': [],
    }

    ALL_CONFIG_DEFAULTS = {**CONFIG_DEFAULTS, **LEAF_CONFIG_DEFAULTS}

    def __init__(self, **kwargs):
        for key, default in self.ALL_CONFIG_DEFAULTS.items():
            val = kwargs.get(key, default)
            setattr(self, key, copy.deepcopy(val))

        self.sanitize_do_arguments()
        self.filter_expansions()

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

        for key in ['kwargs', 'directory_expansions', 'prefix_expansions', 'suffix_expansions']:
            config[key].update(collection.get(key, {}))

        config.update({k: v for k, v in collection.items() if k in config['item_type'].LEAF_CONFIG_DEFAULTS})

        return config

    @classmethod
    def sanitize_parent_config(cls, config):
        """
        a parent config should have only Item.CONFIG_DEFAULTS keys
        """
        new_config = {}
        for key, default in cls.CONFIG_DEFAULTS.items():
            val = config.get(key, default)
            new_config[key] = copy.deepcopy(val)

        return new_config

    @classmethod
    def from_config(cls, config):
        item_type = config.pop('item_type')
        return item_type(**config)

    def sanitize_do_arguments(self):
        (_args, _varargs, _kwargs, _, _, _, _) = inspect.getfullargspec(self.do)

        # don't sanitize args if the function has dynamic arguments
        if _varargs or _kwargs:
            return

        for arg_store_name in ['kwargs', 'directory_expansions', 'prefix_expansions', 'suffix_expansions']:
            arg_store = getattr(self, arg_store_name)
            arg_store = {k: v for k, v in arg_store.items() if k in _args}
            setattr(self, arg_store_name, arg_store)

    def filter_expansions(self):
        """
        get rid of expansions that are in conflict with `kwargs`
        """
        for arg_store_name in ['directory_expansions', 'prefix_expansions', 'suffix_expansions']:
            arg_store = getattr(self, arg_store_name)

            for key, val in self.kwargs.items():
                if key in arg_store:
                    arg_store[key] = [val]

            setattr(self, arg_store_name, arg_store)

        self.expansion_keys_by_type = {
            'directories': list(self.directory_expansions.keys()),
            'prefixes': list(self.prefix_expansions.keys()),
            'suffixes': list(self.suffix_expansions.keys()),
        }

    @property
    def location(self):
        return "/".join(self.path_components)

    @property
    def name(self):
        return self.path_components[-1]

    @property
    def collection(self):
        return self.path_components[:-1]

    @property
    def directory(self):
        return Path(*self.collection)

    def get_expansion_composition(self, kwargs):
        # go in expansion order (rather than kwargs order) because then output is always predictable
        expansion_composition = defaultdict(list)
        for expansion_type, keys in expansion_keys_by_type.items():
            for key in [key for key in keys if key in kwargs]:
                expansion_composition[expansion_type].append(kwargs[key])

        return expansion_composition

    @cached_property
    def expansions(self):
        all_options = {**keys for keys in self.expansion_keys_by_type}

        expansions = []
        for option_set in itertools.product(*list(all_options.values())):
            kwargs = copy.deepcopy(self.kwargs)

            index = 0
            for keys in self.expansion_keys_by_type.values():
                kwargs.update({k: option_set[index + i] for i, k in enumerate(keys)})
                index += len(keys)

            expansions.append(Expansion(item=self, kwargs=kwargs))

        return expansions

    def get_matching_expansions(self, kwargs):
        matching_expansions = []
        for expansion in self.expansions:
            if all([expansion.kwargs[k] == v for k, v in kwargs.items()]):
                matching_expansions.append(expansion)

        return matching_expansions

    @staticmethod
    def parse_query(query):
        return query.split('/')

    def query_matches(self, query):
        """
        There are several ways to match a query:
        1. exact: the full path to 

        1. path
        2. name

        how did things match?
        - partial
        - complete

        for partial matches, where?
        - start
        - end

        returns a dict:
        {
            'full': True/False
            'name': "complete"/"start"/"mismatch",
            'collection': "complete"/"start"/"partial"/"mismatch",
        }
        """
        parsed_query = self.parse_query(query)
        qname = parsed_query[-1]
        qcollection = parsed_query[:-1]

        return {
            'full': "/".join(self.path_components) == query,
            'name': self.query_matches_name(qname),
            'collection': self.query_matches_collection(qcollection, parse=False)
        }

    def query_matches_name(self, query):
        if self.name == query:
            return "complete"
        elif self.name.startswith(query):
            return "start"
        else:
            return "mismatch"

    def query_matches_collection(self, query, parse=True):
        if parse:
            query = self.parsed_query(query)

        if self.query_matches_collection_exactly(query):
            if len(query) == len(self.collection):
                return "complete"
            else:
                return "start"
        elif recursive_query_matches_collection(query, self.collection):
            return "partial"
        else:
            return "mismatch"

    def query_matches_collection_exactly(self, query):
        return all([q == c for q, c in zip(query, self.collection)])

    @staticmethod
    def recursive_query_matches_collection(query, collection):
        if not collection:
            return True

        for i, query_part in enumerate(query):
            if collection[0].startswith(query_part):
                return Item.recursive_query_matches_collection(query[i + 1:], collection[1:])

        return False


class PlotItem(Item):
    SUFFIXES = ['.png', '.pdf']

    def save(self, result, path, show=False, dpi=400):
        path = str(path)

        plt.savefig(path, dpi=dpi, bbox_inches='tight')
        plt.clf()
        plt.close()

        if show:
            os.system(f'open "{path}"')


class DataFrameItem(Item):
    SUFFIXES = ['.gz', '.csv']

    LEAF_CONFIG_DEFAULTS = {
        **Item.LEAF_CONFIG_DEFAULTS,
        'formatter': lambda df: df.copy(),
    }

    ALL_CONFIG_DEFAULTS = {**Item.CONFIG_DEFAULTS, **LEAF_CONFIG_DEFAULTS}

    def save(self, result, path):
        result.to_csv(path, index=False)


class JSONItem(Item):
    SUFFIXES = ['.json']

    def save(self, result, path):
       path.write_text(json.dumps(result, indent=4, sort_keys=True))


class Runner(object):
    def __init__(
        self,
        collection={},
        directory=Path.cwd().joinpath('results'),
        default_item_type=Item,
    ):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True, parents=True)

        self.default_item_type = default_item_type

        self.items = self.parse_collection(
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

    def get_item(self, query):
        """
        we want to be as generous as possible when responding to names, because
        sometimes we won't always want to fully specify a name.

        any time we can get a single match, we should return that match.

        Let's always assume that the last part is the "stem" (in pathlib terminology).

        I could see calling this in multiple ways:
        1. /[first letter of first dir]/[second letter of second dir]/name
        """
        results = [(i, i.query_matches(query)) for i in self.items]

        full_matches = [i for i, result in results if i['full']]

        if len(full_matches) == 1:
            return full_matches[0]
        else:
            print("this shouldn't happen")
            raise AmbiguousCollectionQuery
            
        name_matches = [r for r in results if r[1]['name'] == 'complete']

        if len(name_matches) == 1:
            return name_matches[0][0]
        else:
            results = name_matches

        for status in ["complete", "start", "partial"]:
            status_results = [r for r in results if r[1]['collection'] == status]

            if len(status_results) == 1:
                return status_results[0][0]

        raise AmbiguousCollectionQuery

    def get_items_in_collection(self, query):
        """
        we require a full "start" match for collection queries
        """
        results = []
        for item in self.items:
            if item.query_matches_collection(query) in ['complete', 'start']:
                results.append(item)

        return results

    ################################################################################
    #
    #
    # running
    #
    #
    ################################################################################
    def run_all(self, **kwargs):
        for item in self.items:
            print(item.location)
            self.run_item(
                item=item,
                run_expansions=True,
                **kwargs
            )

    def run_subcollection(self, query, run_expansions=True, **kwargs):
        for item in self.get_items_in_collection(query):
            print(item.location)
            self.run_item(
                item=item,
                run_expansions=run_expansions,
                **kwargs
            )

    def run(
        self,
        query,
        **kwargs,
    ):
        item = self.get_item(query)
        self.run_item(item, **kwargs)

    def run_item(
        self,
        item,
        save_kwargs={},
        run_expansions=False,
        **kwargs,
    ):
        expansions = item.get_matching_expansions(**kwargs)

        if not run_expansions:
            expansions = [:1]

        for expansions in expansions:
            expansion.save(
                result=item.do(**expansion.kwargs),
                directory=self.directory,
                **save_kwargs,
            )

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
