from functools import lru_cache
import random
from typing import Iterable, List, Tuple, Callable

class PickTree(dict):
    cached: bool    # True if the adjusted weights at that node have been cached
    path: tuple     # The path from the root to this node
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
    weights: Tuple[Tuple[float]]    # Weights for each layer (each layer sums to 1.0)
    layer_cnt: int                  # Number of layers
    var_cnt: List[int]              # Number of variations for each layer
    random_range: List[int]         # Range for the random number generated
    seed: str                       # Seed for the random number generator
    all_picks: List[Tuple[int]]     # List of all picks
    picks_tree: PickTree            # The pick tree
    cache_dict: dict                # Cache for the adjusted weights calculation
    progress_cb: Callable[[int, int], None] # A progress callback function
    validation_cb: Callable[[Tuple[int]], bool] # A validation callback function for picks
    validate_each_layer: bool       # True if the validation callback should be called for each layer

    def __init__(self, weights: Iterable[Iterable[float]], seed: str = None):
        assert all(
            [abs(sum(w) - 1.0) < 1e-10 for w in weights]
        ), "Weights in a layer must sum to 1.0"
        self.weights = tuple([ tuple([ w for w in layer_weights]) for layer_weights in weights ])
        self.layer_cnt = len(weights)
        self.random_range = [0, 100**self.layer_cnt]

        self.var_cnt = [len(w) for w in weights]

        self.seed = seed
        random.seed(self.seed)
        self.all_picks = []
        # Tree with previous picks represented as branches (leafs are picks that should have probability 0 for the next pick)
        # Branches can be of length 0 < n <= layer_cnt
        # keys: 1, 2, ... n are children
        # If no keys are present, it's a leaf
        # If attribute path is None, it's the root
        # Depth is the number of layers (layer_cnt)
        self.picks_tree = PickTree()
        self.picks_tree.path = None

        self.progress_cb = None
        self.set_validation_callback(lambda pick: True)

        self.cache_dict = {}

    # Add a pick to the pick tree and invalidate cache if necessary
    # pick can be any length n > 0, which will create a branch of length n
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

    # Add a list of samples (aka picks) to the pick tree
    def add_samples(self, picks: Iterable[Tuple[int]]) -> None:
        if picks is None:
            return
        for pick in picks:
            self.add_pick(self.picks_tree, pick)
            self.all_picks.append(pick)

    # Recursively compute the adjusted weights for a given layer variations based on the pick tree
    def adjusted_weights(self, picks_node: PickTree, layer: int=0) -> Tuple:
        if picks_node is None: # Outside of the tree (i.e. no previous picks in that branch)
            return self.weights[layer]
        if len(picks_node.keys()) == 0 and picks_node.path is not None:  # Is this a leaf?
            if layer >= self.layer_cnt:
                return tuple([0])
            return tuple([0] * len(self.weights[layer]))  # The probability of a leaf that has already been picked is 0 for all children
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

    # Set the progress callback function
    def set_progress_callback(self, callback: Callable[[int, int], None]) -> bool:
        if isinstance(callback, Callable):
            self.progress_cb = callback
            return True
        return False

    # Set a validation callback function for picks. The callback function should return True if the pick is valid, False otherwise
    # If validate_each_layer is True, the callback function will be called for each layer. Otherwise, the callback function will be called once all layers have been picked
    def set_validation_callback(self, callback: Callable[[Tuple[int]], bool], validate_each_layer: bool=False) -> bool:
        if isinstance(callback, Callable):
            self.validation_cb = callback
            self.validate_each_layer = validate_each_layer
            return True
        return False

    # Sample unique random picks without replacement
    def sample(self, count: int, ids: Iterable[int] = None) -> List[Tuple[int]]:
        if ids:
            assert len(ids) == count, "Number of ids must match the number of samples"

        for i in range(count):
            # Progress callback
            if self.progress_cb and (count >= 100) and (i % 100 == 0):
                self.progress_cb(i, count)
            # Seed randomness based on ids if provided
            if ids:
                random.seed(f"{self.seed}{ids[i]}")

            # Find a valid pick randomly
            pick_valid = False
            while not pick_valid:
                # Sample enough randomness for all layers at once
                r = random.randrange(*self.random_range)
                picks_tree_current = self.picks_tree
                new_pick = []
                # odds = []
                for j in range(self.layer_cnt): # For each layer
                    # Compute adjusted weights based on the pick tree
                    adj_weights = self.adjusted_weights(picks_tree_current, j)
                    # odds.append(adj_weights)
                    adj_ratio =  sum(adj_weights)
                    # Determine the variation based on randomness
                    cweights = cum_weights(adj_weights) # Cumulative weights for the current layer
                    layer_rand = (r % 100) / 100 * adj_ratio
                    r //= 100
                    index = [i for i, cw in enumerate(cweights) if cw > layer_rand][0]
                    new_pick.append(index)

                    # Check if the pick is already invalid
                    if self.validate_each_layer and not self.validation_cb(tuple(new_pick)):
                        self.add_pick(self.picks_tree, tuple(new_pick)) # Add the pick to the pick tree to avoid it being picked again
                        break

                    if picks_tree_current and index in picks_tree_current: # Progress down the tree
                        picks_tree_current = picks_tree_current[index]
                    else:
                        picks_tree_current = None # Outside of the tree

                # Check if the new pick is valid
                pick_valid = self.validation_cb(tuple(new_pick))
                # if not pick_valid:
                #     print("Invalid pick:", new_pick)

            new_pick = tuple(new_pick)
            assert new_pick not in self.all_picks, "Duplicate pick"

            # Add the new pick to the pick tree
            self.add_pick(self.picks_tree, new_pick)
            # print(f"Picked: {new_pick} with odds {odds}")

            self.all_picks.append(new_pick)

        if self.progress_cb:
            self.progress_cb(count, count)
        return self.all_picks[-count:]