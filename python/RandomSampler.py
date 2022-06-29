from functools import lru_cache
import random
from typing import Iterable, List, Tuple

class PickTree(dict):
    cached: bool
    path: tuple
    def list_instance_attributes(self):
        inst_attr = []
        for attribute, value in self.__dict__.items():
            inst_attr.append(f"{attribute}={value}")
        return inst_attr
    def __repr__(self):
        return f"PickTree(attr=({', '.join(self.list_instance_attributes())}), {super().__repr__()})"

# Helper function to compute the cumulative weights from a list of weights (cached)
@lru_cache(maxsize=256)
def cum_weights(weights: tuple) -> tuple:
    return tuple([sum(weights[:i+1]) for i in range(len(weights))])

class RandomSampler:
    weights: Tuple[Tuple[float]]
    layer_cnt: int
    random_range: int
    var_cnt: int
    all_picks: List[Tuple[int]]
    picks_tree: PickTree
    cache_dict: dict

    def __init__(self, weights: Iterable[Iterable[float]], seed: str = None):
        assert all(
            [abs(sum(w) - 1.0) < 1e-10 for w in weights]
        ), "Weights in a layer must sum to 1.0"
        self.weights = tuple([ tuple([ w for w in layer_weights]) for layer_weights in weights ])
        self.layer_cnt = len(weights)
        self.random_range = [0, 100**self.layer_cnt]

        self.var_cnt = [len(w) for w in weights]

        random.seed(seed)
        self.all_picks = []
        # Tree with previous picks
        # keys: 1, 2, ... n are children
        # If no keys are present, it's a leaf
        # If attribute path is None, it's the root
        # Depth is the number of layers (layer_cnt)
        self.picks_tree = PickTree()
        self.picks_tree.path = None

        self.cache_dict = {}

    def adjusted_weights(self, picks_node: PickTree, layer: int=0) -> Tuple:
        if picks_node is None:
            return self.weights[0]
        if len(picks_node.keys()) == 0 and picks_node.path is not None:  # Is this a leaf?
            return tuple([0])  # The probability of a leaf that has already been picked is 0
        adj_weights = list(self.weights[layer]) # Adjusted weights
        for i in range(len(adj_weights)):
            if i in picks_node:
                if tuple([picks_node.path, i]) in self.cache_dict and picks_node[i].cached:
                    adj_weights[i] *= self.cache_dict[tuple([picks_node.path, i])]
                else:
                    self.cache_dict[tuple([picks_node.path, i])] = sum(self.adjusted_weights(picks_node[i], layer+1))
                    adj_weights[i] *= self.cache_dict[tuple([picks_node.path, i])]
                    picks_node[i].cached = True
        return tuple(adj_weights)

    def add_pick(self, picks_node: PickTree, pick: Tuple[int], layer: int=0) -> bool:
        if layer == len(pick):  # Leaf reached
            return picks_node.cached
        var_pick = pick[layer]
        # Create new branch if necessary, new branches are marked as not cached
        if var_pick not in picks_node:
            picks_node[var_pick] = PickTree()
            picks_node[var_pick].cached = False
            picks_node[var_pick].path = pick[:layer+1]
        # Recurse down the tree. Mark the node as not cached if the branch we explored was not cached
        if not self.add_pick(picks_node[var_pick], pick, layer+1):
            picks_node.cached = False
            if picks_node.path:
                self.cache_dict.pop(tuple([picks_node.path[:-1], picks_node.path[-1]]), None)
        return picks_node.cached

    def add_samples(self, picks: Iterable[Tuple[int]]) -> None:
        if picks is None:
            return
        for pick in picks:
            self.add_pick(self.picks_tree, pick)
            self.all_picks.append(pick)

    def sample(self, count: int) -> List[Tuple[int]]:
        for i in range(count):
            r = random.randrange(*self.random_range)
            picks_tree_current = self.picks_tree
            new_pick = []
            odds = []
            for j in range(self.layer_cnt):
                adj_weights = self.adjusted_weights(picks_tree_current, j)
                # odds.append(adj_weights)
                adj_ratio =  sum(adj_weights)
                cweights = cum_weights(adj_weights) # Cumulative weights for the current layer
                layer_rand = (r % 100) / 100 * adj_ratio
                r //= 100

                index = [i for i, cw in enumerate(cweights) if cw > layer_rand][0]
                new_pick.append(index)
                if picks_tree_current and index in picks_tree_current:
                    picks_tree_current = picks_tree_current[index]
                else:
                    picks_tree_current = None # Outside of the tree

            new_pick = tuple(new_pick)
            assert new_pick not in self.all_picks, "Duplicate pick"

            self.add_pick(self.picks_tree, new_pick)
            # print(f"Picked: {new_pick} with odds {odds}")

            self.all_picks.append(new_pick)

        return self.all_picks[-count:]