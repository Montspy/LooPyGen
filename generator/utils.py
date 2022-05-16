
from dataclasses import dataclass
from typing import TypeVar, Generic
from collections import OrderedDict
from glob import glob
import json
import os
import re

@dataclass
class Struct(dict):
    def __init__(self, d: dict = None):
        if d:
            for k,v in d.items():
                super().__setitem__(k,v)
    def __getattr__(self, name):
        if super().__contains__(name):
            return super().__getitem__(name)
        else:
            return None
    def __setattr__(self, name, value):
        return super().__setitem__(name, value)
    def __delattr__(self, name):
        return super().__delitem__(name)
    def __str__(self):
        return super().__str__()
    def __repr__(self):
        return super().__repr__()


def load_traits(name: str = None):
    traits_path = ""
    if name:
        traits_path = os.path.join("./collections", name, "config", "traits.json")
    else:
        all_jsons = glob("./collections/*/config/traits.json")
        all_names = []
        for f in all_jsons:
            with open(f, 'r') as j:
                all_names.append(json.load(j).get("collection_name", "Unknown collection name"))
        assert len(all_names) > 0, "Found 0 existing collections in ./collections"

        print(f"Found {len(all_names)} collections:\n  " + "\n  ".join( [ f"{i+1}. {n}" for i,n in enumerate(all_names)] ))
        while True:
            print(f"Pick one (1~{len(all_names)}): ", end="")
            s = input().lower()
            try:
                s = int(s)
            except ValueError as err:
                continue
            if (s > 0) and (s <= len(all_names)):
                break
        traits_path = all_jsons[s - 1]

    with open(traits_path) as f:
        traits_json = json.load(f)
    return Struct(traits_json)

def load_config(paths: Struct):
    with open(paths.config) as f:
        config_json = json.load(f)
    return Struct(config_json)

def generate_paths(traits: Struct):
    paths = Struct()
    paths.collection = os.path.join("./collections", traits.collection_lower)
    paths.ipfs_folder = os.path.join(paths.collection, "ipfs")
    paths.metadata = os.path.join(paths.ipfs_folder, "metadata")
    paths.images = os.path.join(paths.ipfs_folder, "images")
    paths.thumbnails = os.path.join(paths.ipfs_folder, "thumbnails")

    paths.gen_conf = os.path.join(paths.collection, "config")
    paths.source = os.path.join(paths.gen_conf, "source_layers")
    paths.metadata_cids = os.path.join(paths.gen_conf, "metadata-cids.json")

    paths.stats = os.path.join(paths.collection, "stats")
    paths.all_traits = os.path.join(paths.stats, "all-traits.json")
    paths.gen_stats = os.path.join(paths.stats, "gen-stats.json")

    paths.config = "./config.json"

    return paths

def get_variation_cnt(layers: list):
    cnt = 1
    for layer in layers:
        cnt *= len(layer["weights"])
    return cnt

# JSON conversion
class SemVerFilter(object):
    regex = r"^(?P<major>x|0|[1-9]\d*)\.(?P<minor>x|0|[1-9]\d*)\.(?P<patch>x|0|[1-9]\d*)?$"
    filter: str
    elements: list
    priority: int   # Lower number means higher priority
    match_regex: str

    def __init__(self, ver_filter: str):
        self.filter = ver_filter.replace("v", "").strip()
        # Extract major, minor, patch elements
        m = re.match(self.regex, self.filter)
        assert m is not None, f"Invalid version filter {ver_filter}"
        self.elements = [m.group('major'), m.group('minor'), m.group('patch')]

        # Validate wildcard position, calculate priority rank
        wildcard_found = False
        self.priority = 0
        for i,el in enumerate(self.elements):
            if wildcard_found and el != "x":
                raise Exception(f"Invalid version filter, numeral found after wildcard {ver_filter}")
            elif el == "x":
                if not wildcard_found:
                    self.priority = 3 - i
                wildcard_found = True
        
        self.match_regex = r"^" + r"\.".join(self.elements).replace('x', r"(0|[1-9]\d*)") + r"$"

        super().__init__()

    def get_priority(self) -> int:
        return self.priority

    def match(self, ver: 'SemVerFilter') -> bool:
        assert ver.get_priority() == 0, f"SemVerFilter cannot match to version with wildcard {ver}"
        return re.match(self.match_regex, ver.filter) is not None

    def __repr__(self) -> str:
        return f"{self.elements[0]}.{self.elements[1]}.{self.elements[2]}"

    def __hash__(self) -> int:
        return hash((self.elements[0], self.elements[1], self.elements[2]))

class FromToFilter(object):
    def __init__(self, f: SemVerFilter, t: SemVerFilter) -> None:
        self.f = f
        self.t = t
        super().__init__()

    def get_priority(self) -> int:
        return self.f.get_priority() + self.t.get_priority()
    
    def sort_func(self) -> int:
        return self.get_priority()

    def match(self, fromto: 'FromToFilter') -> bool:
        return self.f.match(fromto.f) and self.t.match(fromto.t)

    def __repr__(self) -> str:
        return f"{self.f} -> {self.t}"

    def __hash__(self):
        return hash((self.f, self.t))

Key = TypeVar('Key', bound=FromToFilter)
Route = TypeVar('Route')

class Router(Generic[Key, Route]):
    routes: 'OrderedDict[Key, Route]'

    def __init__(self) -> None:
        self.routes = OrderedDict()
        super().__init__()

    def add_map(self, key: Key, route: Route) -> None:
        self.routes[key] = route
        s = sorted(self.routes.items(), key=lambda kv_pair: kv_pair[0].sort_func())
        self.routes = OrderedDict(s)

    def match_route(self, filter: FromToFilter) -> Route:
        for key, route in self.routes.items():
            if key.match(filter):
                return route
        
        return None

# [END] JSON conversion