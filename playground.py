from functools import lru_cache, reduce
from math import log2
from pprint import pprint
import random
import sys

weights = [
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
    [2] * 50,
]
# weights = [
#     [17, 21, 12, 50],
#     [25, 25, 25, 25]
# ]

weights = tuple([tuple([w / 100 for w in ws]) for ws in weights])
# pprint(weights)

layer_cnt = len(weights)
var_cnt = [len(w) for w in weights]

assert all(
    [abs(sum(w) - 1.0) < 1e-10 for w in weights]
), "Weights in a layer must sum to 1.0"

print(f"Layer count: {layer_cnt}")
print(f"Variations count per layer: {var_cnt}")
total_var_cnt = reduce(lambda x, y: x * y, var_cnt, 1)
print(f"Total combinations: {total_var_cnt} (aka {total_var_cnt:.1E})")
print(f"Minimum precision: {100**len(var_cnt):.1E} ({log2(100**len(var_cnt))} bits)")

random_range = 100**layer_cnt

sample_cnt = min(10000, total_var_cnt)
print(f"Sampling {sample_cnt} random variations")
print(f"Random range: {random_range} (aka {random_range:.1E})")

random.seed("toast")

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

adj_weights_cache_dict = {}
def adjusted_weights(picks_node: PickTree, orig_weights: tuple, layer: int=0) -> tuple:
    if picks_node is None:
        # print("None, returning orig_weights[0]")
        return orig_weights[0]
    if len(picks_node.keys()) == 0 and picks_node.path is not None:  # Is this a leaf?
        # print("Leaf, returning [0]")
        return tuple([0])  # The probability of a leaf that has already been picked is 0
    # print(*[' ']*layer*2, f"Adjusting weights, layer {layer}")
    # print(*[' ']*layer*2, f"orig_weights ", end=''); pprint(orig_weights)
    # print(*['  ']*layer*2, end=''); pprint(picks_tree)
    adj_weights = list(orig_weights[layer]) # Adjusted weights
    for i in range(len(adj_weights)):
        if i in picks_node:
            # print(*[' ']*layer*2, f"Has children '{i}'")
            if tuple([picks_node.path, i]) in adj_weights_cache_dict and picks_node[i].cached:
                # print('cached')
                adj_weights[i] *= adj_weights_cache_dict[tuple([picks_node.path, i])]
            else:
                adj_weights_cache_dict[tuple([picks_node.path, i])] = sum(adjusted_weights(picks_node[i], orig_weights, layer+1))
                adj_weights[i] *= adj_weights_cache_dict[tuple([picks_node.path, i])]
                picks_node[i].cached = True
            # adj_weights[i] *= sum(adjusted_weights(PickTree(picks_tree[i]), orig_weights[1:], layer+1))
    # print(*[' ']*layer*2, f"Adjusted weights: {adj_weights}")
    return tuple(adj_weights)

def add_pick_to_tree(picks_node: PickTree, pick: tuple, orig_weights:tuple, layer: int=0) -> bool:
    if layer == len(pick):  # Leaf reached
        return picks_node.cached
    var_pick = pick[layer]
    # Create new branch if necessary, new branches are marked as not cached
    if var_pick not in picks_node:
        picks_node[var_pick] = PickTree({})
        picks_node[var_pick].cached = False
        picks_node[var_pick].path = pick[:layer+1]
    # Recurse down the tree. Mark the node as not cached if the branch we explored was not cached
    if not add_pick_to_tree(picks_node[var_pick], pick, orig_weights, layer+1):
        picks_node.cached = False
        if picks_node.path:
            adj_weights_cache_dict.pop(tuple([picks_node.path[:-1], picks_node.path[-1]]), None)
    return picks_node.cached

def sample_variations():
    random.seed('toast')
    try:
        all_picks = set()
        # Tree with previous picks
        # keys: 1, 2, ... n are children
        # If no keys are present, it's a leaf
        # If attribute path is None, it's the root
        # Depth is the number of layers (layer_cnt)
        picks_tree = PickTree({})
        picks_tree.path = None
        for i in range(sample_cnt):
            r = random.randrange(0, random_range)
            picks_tree_current = picks_tree
            new_pick = []
            odds = []
            for j in range(layer_cnt):
                # print(f"Layer {j}")
                adj_weights = adjusted_weights(picks_tree_current, weights, j)
                # print(f"Adjusted weights: {adj_weights}")
                odds.append(adj_weights)
                adj_ratio =  sum(adj_weights)
                cweights = [sum(adj_weights[:i+1]) for i in range(len(adj_weights))] # Cumulative weights for the current layer
                layer_rand = (r % 100) / 100 * adj_ratio
                r //= 100

                index = [i for i, cw in enumerate(cweights) if cw > layer_rand][0]
                new_pick.append(index)
                if picks_tree_current and index in picks_tree_current:
                    picks_tree_current = picks_tree_current[index]
                else:
                    picks_tree_current = None # Outside of the tree

            new_pick = tuple(new_pick)
            assert new_pick not in all_picks, "Duplicate pick"

            add_pick_to_tree(picks_tree, new_pick, weights)
            # print(f"Picked: {new_pick} with odds {odds}")

            all_picks.add(new_pick)
    finally:
        print(len(all_picks))
        # import json
        # with open('samples.json', 'w+') as f:
        #     json.dump([list(pick) for pick in all_picks], f)
        # print(all_picks)
        print(frozenset(all_picks).__hash__())
        # pprint(picks_tree, indent=4)
        pass

from timeit import repeat
setup_code = "from __main__ import sample_variations"
stmt = "sample_variations()"
times = repeat(setup=setup_code, stmt=stmt, repeat=1, number=1)
print(f"Minimum execution time: {min(times)}")

# sample_variations()

# for j in range(layer_cnt):
#     hist, _ = np.histogram(samples[j], bins=var_cnt[j])
#     print([h / sample_cnt * 100 for h in hist])
