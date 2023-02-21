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
# - allow for not writing the full terminal path if there is only one match for
# the path
# - in `get`, have option to rerun:
#     - shallowly: just the item called
#     - deeply: rerun everything it calls
# - have boolean args convert to "{param}"/"not-{param}" in paths
# - support conditional expansions:
#   - make a ConditionalExpansion object:
#         'some_arg_with_conditions': ConditionalType([list, of, values, to, expand], {
#             'arg_with_condition1': required_arg_value,
#             'arg_with_condition2': [list, of, valid, arg, values],
#         }),
#   - requires modifying:
#       - Item.filter_expansions()
#           - convert all expansions into standard format (no conditions)
#           - move constraints into "constraints_by_key"
#       - Item.get_expansions()
#       - Item.expansions
#           - filter expansions by "constraints_by_key"

class AmbiguousCollectionQuery(Exception):
    pass

class ItemNotFound(Exception):
    pass

class AmbiguousExpansionQuery(Exception):
    pass

class MultipleExpansionsFound(Exception):
    pass

class ExpansionNotFound(Exception):
    pass


class Expansion(object):
    SHORT_NAME = 'expansion'
    SUFFIXES = ['.txt']

    ARG_SEP = '-'
    LIST_VAL_SEP = '+'
    DICT_KEY_VAL_SEP = '='

    """
    an Expansion is an instantiation of an Item — basically, a single expansion
    """
    def __init__(self, item, do, kwargs):
        self.item = item
        self.do = do
        self.kwargs = kwargs

    def __repr__(self):
        return f"Expansion: {str(self.path).replace(str(self.item.results_dir) + '/', '')}"

    @cached_property
    def name(self):
        # iterate over expansions (rather than kwargs) so order is consistent
        parts = [self.kwargs[k] for k in self.item.prefix_expansions if k in self.kwargs]

        if not self.item.as_directory:
            parts.append(self.item.name)

        # iterate over expansions (rather than kwargs) so order is consistent
        parts += [self.kwargs[k] for k in self.item.suffix_expansions if k in self.kwargs]

        parts = [self.stringify_arg(p) for p in parts]

        return self.ARG_SEP.join(parts) or self.ARG_SEP

    @cached_property
    def directory(self):
        # iterate over expansions (rather than kwargs) so order is consistent
        parts = []

        if self.item.as_directory:
            parts.append(self.item.name)

        parts += [self.kwargs[k] for k in self.item.directory_expansions if k in self.kwargs]
        parts += self.item.subdirs

        parts = [self.stringify_arg(p) for p in parts]

        return self.item.directory.joinpath(*parts)

    @classmethod
    def stringify_arg(cls, arg):
        if isinstance(arg, list):
            str_arg = cls.LIST_VAL_SEP.join([str(val) for val in arg])
        elif isinstance(arg, dict):
            str_arg = cls.LIST_VAL_SEP.join([str(k) + cls.DICT_KEY_VAL_SEP + str(v) for k, v in arg.items()])
        else:
            str_arg = str(arg)
        
        return str_arg

    @property
    def path(self):
        return self.directory.joinpath(self.name).with_suffix(self.item.suffix)

    def run(self, save_kwargs={}, **kwargs):
        result = self.do(**{
            **self.kwargs,
            **kwargs,
        })

        self.save(result, **save_kwargs)

        return result

    @property
    def result(self):
        return self.path

    def save(self, result, **kwargs):
        self.path.parent.mkdir(exist_ok=True, parents=True)


class PlotExpansion(Expansion):
    SHORT_NAME = 'plot'
    SUFFIXES = ['.png', '.pdf', '.eps']

    def save(self, result, dpi=400, bbox_inches='tight'):
        self.path.parent.mkdir(exist_ok=True, parents=True)

        plt.savefig(self.path, dpi=dpi, bbox_inches=bbox_inches)
        plt.clf()
        plt.close()

    @property
    def result(self):
        os.system(f'open "{str(self.path)}"')


class InteractivePlotExpansion(Expansion):
    SHORT_NAME = 'plot'
    SUFFIXES = ['.png', '.pdf', '.eps']

    def save(self, result, dpi=400, bbox_inches='tight'):
        self.path.parent.mkdir(exist_ok=True, parents=True)
        plt.show()

    @property
    def result(self):
        os.system(f'open "{str(self.path)}"')


class DataFrameExpansion(Expansion):
    SHORT_NAME = 'df'
    SUFFIXES = ['.gz', '.csv']

    @property
    def result(self):
        return pd.read_csv(self.path)

    def save(self, result, **kwargs):
        self.path.parent.mkdir(exist_ok=True, parents=True)
        result.to_csv(self.path, index=False)


class JSONExpansion(Expansion):
    SHORT_NAME = 'json'
    SUFFIXES = ['.json']

    @property
    def result(self):
        return json.loads(self.path.read_text())

    def save(self, result, **kwargs):
        self.path.parent.mkdir(exist_ok=True, parents=True)
        self.path.write_text(json.dumps(result, indent=4, sort_keys=True))


class Item(object):
    """
    an item is an element in a collection that gets fed to a Runner.

    it defines:
    - what an element in a collection looks like: the set of keys it supports
    - what to do with a result
    - how to save it
    """
    EXPANSION_TYPE = Expansion

    CONFIG_DEFAULTS = {
        'results_dir': Path.cwd().joinpath('results'),
        'path_components': [],
        'kwargs': {},
        'arg_defaults': {},
        'directory_expansions': {},
        'prefix_expansions': {},
        'suffix_expansions': {},
        'expansion_type': Expansion,
    }

    LEAF_CONFIG_DEFAULTS = {
        'do': lambda: None,
        'subdirs': [],
        'aliases': [],
        'as_directory': False,
    }

    ALL_CONFIG_DEFAULTS = {**CONFIG_DEFAULTS, **LEAF_CONFIG_DEFAULTS}

    ARG_STORE_NAMES = [
        'kwargs',
        'arg_defaults',
        'directory_expansions',
        'prefix_expansions',
        'suffix_expansions',
    ]

    def __init__(self, **kwargs):
        for key, default in self.ALL_CONFIG_DEFAULTS.items():
            val = kwargs.get(key, default)
            setattr(self, key, copy.deepcopy(val))

        self.expansion_type = kwargs.get('expansion_type', self.EXPANSION_TYPE)

        self.set_suffix()

        self.sanitize_do_arguments()
        self.filter_expansions()
        self.set_arg_defaults()

    def __eq__(self, other):
        conditions = []
        for key in self.ALL_CONFIG_DEFAULTS:
            conditions.append(getattr(self, key) == getattr(other, key))

        return all(conditions)

    def __repr__(self):
        return f"{type(self).__name__}: {self.location}"

    def set_suffix(self, suffix=None):
        self.suffix = suffix or self.expansion_type.SUFFIXES[0]

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
        - use data in `collection` to update: config defaults
        """
        config = cls.sanitize_parent_config(config)

        if path:
            config['path_components'].append(path)

        config['expansion_type'] = collection.get('expansion_type', config.get('expansion_type'))
        config['results_dir'] = collection.get('results_dir', config.get('results_dir'))

        for key in cls.ARG_STORE_NAMES:
            config[key].update(collection.get(key, {}))

        config.update({k: v for k, v in collection.items() if k in cls.LEAF_CONFIG_DEFAULTS})

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
        return cls(**config)

    def sanitize_do_arguments(self):
        (_args, _varargs, _kwargs, _, _, _, _) = inspect.getfullargspec(self.do)

        # don't sanitize args if the function has dynamic arguments
        if _varargs or _kwargs:
            return

        for arg_store_name in self.ARG_STORE_NAMES:
            arg_store = getattr(self, arg_store_name)
            arg_store = {k: v for k, v in arg_store.items() if k in _args}
            setattr(self, arg_store_name, arg_store)

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
        return self.results_dir.joinpath(*self.collection)

    @cached_property
    def expansions(self):
        all_options = {}
        for expansion_type, keys in self.expansions_by_type.items():
            all_options.update(keys)

        expansions = []
        for option_set in itertools.product(*list(all_options.values())):
            kwargs = copy.deepcopy(self.kwargs)

            index = 0
            for keys in self.expansion_keys_by_type.values():
                kwargs.update({k: option_set[index + i] for i, k in enumerate(keys)})
                index += len(keys)

            expansions.append(self.expansion_type(item=self, do=self.do, kwargs=kwargs))

        return expansions

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

        self.expansions_by_type = {
            'directories': self.directory_expansions,
            'prefixes': self.prefix_expansions,
            'suffixes': self.suffix_expansions,
        }

    def set_arg_defaults(self):
        for expansions in self.expansions_by_type.values():
            for key, values in expansions.items():
                self.arg_defaults[key] = self.arg_defaults.get(key, values[0])

    def get_expansions(self, **kwargs):
        expansions = []
        for expansion in self.expansions:
            if any([kwargs[k] != v for k, v in expansion.kwargs.items() if k in kwargs]):
                continue
            
            expansions.append(expansion)

        if not expansions:
            raise ExpansionNotFound

        return expansions

    def get_expansion(self, **kwargs):
        for k, v in self.arg_defaults.items():
            if k not in kwargs:
                kwargs[k] = v

        expansions = self.get_expansions(**kwargs)

        if len(expansions) > 1:
            raise MultipleExpansionsFound

        return expansions[0]

    def parsed_query(self, query):
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
        parsed_query = self.parsed_query(query)
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
        elif self.recursive_query_matches_collection(query, self.collection):
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


class Runner(object):
    DEFAULT_EXPANSION_TYPE = Expansion

    ITEM_TYPES = [
        PlotExpansion,
        DataFrameExpansion,
        JSONExpansion,
    ]

    def __init__(
        self,
        collection={},
        directory=Path.cwd().joinpath('results'),
        suffix=None,
    ):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True, parents=True)

        self.items = self.parse_collection(
            collection=collection,
            parent_config={
                'path_components': [],
                'expansion_type': self.DEFAULT_EXPANSION_TYPE,
                'results_dir': self.directory,
            },
        )

        self.suffix = suffix
        self.reset_suffixes()

    def reset_suffixes(self):
        for item in self.items:
            suffix = self.suffix if item.expansion_type == self.DEFAULT_EXPANSION_TYPE else None
            item.set_suffix(suffix)

    def set_suffix(self, suffix, item_type_short_name=None):
        item_type_short_name = item_type_short_name or self.DEFAULT_EXPANSION_TYPE.SHORT_NAME

        for item in self.items:
            if item.expansion_type.SHORT_NAME == item_type_short_name:
                item.set_suffix(suffix)

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

        full_matches = [i for i, result in results if result['full']]

        if len(full_matches) == 1:
            return full_matches[0]
        # else:
        #     raise AmbiguousCollectionQuery
            
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
        self.run_items(self.items, **kwargs)

    def run_collection(self, query, **kwargs):
        self.run_items(self.get_items_in_collection(query), **kwargs)

    def run_items(self, items, **kwargs):
        for item in items:
            print(f"running: {item.location}")
            for expansion in item.get_expansions(**kwargs):
                print(f"\t{expansion.path}")
                expansion.run(**kwargs)

    def run(self, query, **kwargs):
        return self.run_item(self.get_item(query), **kwargs)

    def run_item(
        self,
        item,
        run_expansions=False,
        save_kwargs={},
        **kwargs,
    ):
        expansions = item.get_expansions(**kwargs)

        if not run_expansions:
            expansions = expansions[:1]

        for expansion in expansions:
            expansion.run(save_kwargs=save_kwargs, **kwargs)
            result = expansion.result

        return result

    def get(self, query, rerun=False, save_kwargs={}, **kwargs):
        expansion = self.get_item(query).get_expansion(**kwargs)

        if rerun:
            expansion.path.unlink()

        if expansion.path.exists():
            result = expansion.result
        else:
            print(f"running: {expansion.item.location}")
            result = expansion.run(save_kwargs=save_kwargs, **kwargs)

        return expansion.result

    def get_path(self, query, run_expansions=False, **kwargs):
        expansions = self.get_item(query).get_expansions(**kwargs)

        if not run_expansions:
            expansions = expansions[:1]

        paths = [expansion.path for expansion in expansions]

        if len(paths) == 1:
            return paths[0]

        return paths

    ################################################################################
    #
    #
    # cleaning
    #
    #
    ################################################################################
    def clean(self):
        """
        removes files in the base directories that are not part of the
        collection.
        """
        paths = set()

        for item in self.items:
            for expansion in item.expansions:
                for suffix in expansion.SUFFIXES:
                    paths.add(expansion.path.with_suffix(suffix))

        to_remove = []
        for path in self.directory.rglob('*'):
            if path.is_file() and path not in paths:
                to_remove.append(path)

        for path in to_remove:
            if path.exists():
                path.unlink()

            parent = path.parent
            if not len(list(parent.glob('*'))):
                parent.rmdir()


class PlotRunner(Runner):
    DEFAULT_EXPANSION_TYPE = PlotExpansion

class InteractivePlotRunner(Runner):
    DEFAULT_EXPANSION_TYPE = InteractivePlotExpansion

class DataFrameRunner(Runner):
    DEFAULT_EXPANSION_TYPE = DataFrameExpansion

class JSONRunner(Runner):
    DEFAULT_EXPANSION_TYPE = JSONExpansion
