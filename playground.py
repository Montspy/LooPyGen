from functools import reduce

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

total_var_cnt = reduce(lambda x, y: x * y,  [len(w) for w in weights], 1)
print(f"Total combinations: {total_var_cnt} (aka {total_var_cnt:.1E})")

sample_cnt = min(10000, total_var_cnt)
print(f"Sampling {sample_cnt} random variations")

def sample_variations() -> set:
    from python.RandomSampler import RandomSampler
    rs = RandomSampler(weights, seed='toast')
    samples = rs.sample(sample_cnt)
    print(len(samples))
    print(frozenset(samples).__hash__())


from timeit import repeat
times = repeat(stmt=sample_variations, repeat=1, number=1)
print(f"Minimum execution time: {min(times)}")
