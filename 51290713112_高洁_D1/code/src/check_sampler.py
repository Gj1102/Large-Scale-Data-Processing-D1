"""Check that A1/A2 process the same global indices per full update."""
from torch.utils.data.distributed import DistributedSampler

for epoch in range(3):
    dataset = range(50000)
    samplers = [DistributedSampler(dataset, num_replicas=w, rank=r, seed=42, drop_last=True)
                for w, r in ((1, 0), (2, 0), (2, 1))]
    for sampler in samplers:
        sampler.set_epoch(epoch)
    single, rank0, rank1 = map(list, samplers)
    for i in range(0, len(single) - 127, 128):
        assert set(single[i:i+128]) == set(rank0[i//2:i//2+64] + rank1[i//2:i//2+64])
print('PASS: identical A1/A2 global sample sets for every full update, epochs 0-2')
