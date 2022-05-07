
from dataclasses import dataclass
from glob import glob
import json
import os

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