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

class AmbiguousCollectionQuery(Exception):
    pass

class ItemNotFound(Exception):
    pass

class AmbiguousExpansionQuery(Exception):
    pass

class ExpansionNotFound(Exception):
    pass


class Expansion(object):
    """
    an Expansion is an instantiation of an Item — basically, a single expansion
    """
    def __init__(self, item, do, kwargs, suffix=None):
        self.item = item
        self.do = do
        self.kwargs = kwargs
        self.suffix = suffix or self.SUFFIXES[0]

    def __repr__(self):
        return f"Expansion: {str(self.path).replace(str(self.item.results_dir) + '/', '')}"

    @property
    def path(self):
        expansion_composition = self.item.get_expansion_composition(self.kwargs)

        stem_components = expansion_composition['prefixes']
        stem_components += [self.item.name]
        stem_components += expansion_composition['suffixes']

        stem = "-".join([str(s) for s in stem_components])

        directories = [str(d) for d in expansion_composition['directories']]
        directories += self.item.subdirs

        return self.item.directory.joinpath(*directories, stem).with_suffix(self.suffix)

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
    SUFFIXES = ['.pdf', '.png', '.eps']

    def save(self, result, dpi=400, bbox_inches='tight'):
        self.path.parent.mkdir(exist_ok=True, parents=True)

        plt.savefig(self.path, dpi=dpi, bbox_inches=bbox_inches)
        plt.clf()
        plt.close()

    @property
    def result(self):
        os.system(f'open "{str(self.path)}"')


class DataFrameExpansion(Expansion):
    SUFFIXES = ['.gz', '.csv']

    @property
    def result(self):
        return pd.read_csv(self.path)

    def save(self, result, **kwargs):
        self.path.parent.mkdir(exist_ok=True, parents=True)
        result.to_csv(self.path, index=False)


class JSONExpansion(Expansion):
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
        'directory_expansions': {},
        'prefix_expansions': {},
        'suffix_expansions': {},
        'expansion_type': Expansion,
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

        self.expansion_type = kwargs.get('expansion_type', self.EXPANSION_TYPE)

        self.sanitize_do_arguments()
        self.filter_expansions()

    def __eq__(self, other):
        conditions = []
        for key in self.ALL_CONFIG_DEFAULTS:
            conditions.append(getattr(self, key) == getattr(other, key))

        return all(conditions)

    def __repr__(self):
        return f"{type(self).__name__}: {self.location}"

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

        for key in ['kwargs', 'directory_expansions', 'prefix_expansions', 'suffix_expansions']:
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

        for arg_store_name in ['kwargs', 'directory_expansions', 'prefix_expansions', 'suffix_expansions']:
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

    def get_expansion_composition(self, kwargs):
        # go in expansion order (rather than kwargs order) because then output is always predictable
        expansion_composition = defaultdict(list)
        for expansion_type, keys in self.expansion_keys_by_type.items():
            for key in [key for key in keys if key in kwargs]:
                expansion_composition[expansion_type].append(kwargs[key])

        return expansion_composition

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
        expansions = self.get_expansions(**kwargs)

        if len(expansions) > 1:
            raise AmbiguousExpansionQuery

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
    def run_all(self, save_kwargs={}, **kwargs):
        self.run_items(self.items, **kwargs)

    def run_subcollection(self, query, save_kwargs={}, **kwargs):
        self.run_items(self.get_items_in_collection(query), **kwargs)

    def run_items(self, items, save_kwargs={}, **kwargs):
        for item in items:
            print(f"running: {item.location}")
            for expansion in item.get_expansions(**kwargs):
                expansion.run(save_kwargs=save_kwargs, **kwargs)


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
            expansion.run(**kwargs)
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
            result = expansion.run(save_kwargs={}, **kwargs)

        return expansion.result


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

        for item in self.items.items():
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

class DataFrameRunner(Runner):
    DEFAULT_EXPANSION_TYPE = DataFrameExpansion

class JSONRunner(Runner):
    DEFAULT_EXPANSION_TYPE = JSONExpansion
