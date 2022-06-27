from functools import reduce
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

sample_cnt = min(10000, total_var_cnt // 2)
print(f"Sampling {sample_cnt} random variations")
print(f"Random range: {random_range} (aka {random_range:.1E})")

random.seed("toast")

class HDict(dict):
    def hash_recursive(obj):
        to_be_hashed = []
        for item in obj.items():
            if isinstance(item[1], dict):
                to_be_hashed.append((item[0], HDict.hash_recursive(item[1])))
            elif isinstance(item[1], list):
                to_be_hashed.append((item[0], tuple(item[1])))
            else:
                to_be_hashed.append((item[0], item[1]))
        return hash(frozenset(to_be_hashed))
    def __hash__(self):
        return HDict.hash_recursive(self)

adj_weights_cache_dict = {}
def adjusted_weights(picks_tree: HDict, orig_weights: tuple, layer: int=0) -> tuple:
    if picks_tree is None:
        # print("None, returning orig_weights[0]")
        return orig_weights[0]
    if ('w' in picks_tree) and (len(picks_tree.keys()) == 1):  # Is this a leaf?
        # print("Leaf, returning [0]")
        return tuple([0])  # The probability of a leaf that has already been picked is 0
    # print(*[' ']*layer*2, f"Adjusting weights, layer {layer}")
    # print(*[' ']*layer*2, f"orig_weights ", end=''); pprint(orig_weights)
    # print(*['  ']*layer*2, end=''); pprint(picks_tree)
    adj_weights = list(orig_weights[0]) # Adjusted weights
    for i in range(len(adj_weights)):
        if i in picks_tree:
            # print(*[' ']*layer*2, f"Has children '{i}'")
            if tuple([i, orig_weights]) in adj_weights_cache_dict and picks_tree[i].cached:
                # print('cached')
                adj_weights[i] *= adj_weights_cache_dict[tuple([i, orig_weights])]
            else:
                adj_weights_cache_dict[tuple([i, orig_weights])] = sum(adjusted_weights(HDict(picks_tree[i]), orig_weights[1:], layer+1))
                adj_weights[i] *= adj_weights_cache_dict[tuple([i, orig_weights])]
                picks_tree[i].cached = True
            # adj_weights[i] *= sum(adjusted_weights(HDict(picks_tree[i]), orig_weights[1:], layer+1))


    # print(*[' ']*layer*2, f"Adjusted weights: {adj_weights}")
    return tuple(adj_weights)

def add_pick_to_tree(picks_tree: HDict, pick, orig_weights):
    if len(pick) == 0:
        return picks_tree.cached
    var_pick = pick[0]
    if var_pick not in picks_tree:
        picks_tree[var_pick] = HDict({'w': orig_weights[0][var_pick]})
        picks_tree[var_pick].cached = False
    if not add_pick_to_tree(picks_tree[var_pick], pick[1:], orig_weights[1:]):
        picks_tree.cached = False
    return picks_tree.cached

# print(adjust_weights({}, weights))

# print(adjust_weights({
#     3: {'w': .25,
#         0: {'w': .3,
#             1: {'w': .1,
#                 1: {'w': .5}
#             }
#         },
#         3: {'w': .1,
#             1: {'w': .1,
#                 1: {'w': .5}
#             }
#         },
#     }
# },
# weights))

# sys.exit(0)

# print(adjusted_weights({
#     0: {   0: {'w': 0.25},
#            1: {'w': 0.25},
#            2: {'w': 0.25},
#            3: {'w': 0.25},
#            'w': 0.17},
#     1: {   0: {'w': 0.25},
#            1: {'w': 0.25},
#            2: {'w': 0.25},
#            3: {'w': 0.25},
#            'w': 0.21},
#     2: {   3: {'w': 0.25},
#            'w': 0.12},
#     3: {   0: {'w': 0.25},
#            1: {'w': 0.25},
#            2: {'w': 0.25},
#            3: {'w': 0.25},
#            'w': 0.5}}, weights))

# sys.exit(0)

# samples = []
def sample_variations():
    random.seed('toast')
    try:
        all_picks = set()
        # Tree with previous picks
        # 'w': probability for that node (absent if root)
        # 1, 2, ... n: children
        # If only w is present, it's a leaf
        # If neither w nor 1, 2, ... n is present, it's the root
        # Depth is the number of layers (layer_cnt)
        picks_tree = HDict({})
        for i in range(sample_cnt):
            r = random.randrange(0, random_range)
            picks_tree_current = HDict(picks_tree)
            new_pick = []
            odds = []
            for j in range(layer_cnt):
                # print(f"Layer {j}")
                adj_weights = adjusted_weights(picks_tree_current, weights[j:])
                # print(f"Adjusted weights: {adj_weights}")
                odds.append(adj_weights)
                adj_ratio = 1 / sum(adj_weights)
                cweights = [sum(adj_weights[:i+1]) * adj_ratio for i in range(len(adj_weights))] # Cumulative weights for the current layer
                layer_rand = (r % 100) / 100
                r //= 100

                index = [i for i, cw in enumerate(cweights) if cw > layer_rand][0]
                new_pick.append(index)
                if picks_tree_current and index in picks_tree_current:
                    picks_tree_current = HDict(picks_tree_current[index])
                else:
                    picks_tree_current = None # Outside of the tree

            assert tuple(new_pick) not in all_picks, "Duplicate pick"

            add_pick_to_tree(picks_tree, new_pick, weights)
            # print(f"Picked: {new_pick} with odds {odds}")

            all_picks.add(tuple(new_pick))
    finally:
        print(len(all_picks))
        import json
        # with open('samples.json', 'w') as f:
        #     json.dump([list(pick) for pick in all_picks], f, indent=2)
        # print(all_picks)
        # print(frozenset(all_picks).__hash__())
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
