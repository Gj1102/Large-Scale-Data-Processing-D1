"""Spawn CPU Gloo workers using a unique file store, without torchrun."""
import os
import tempfile
from pathlib import Path
import torch.multiprocessing as mp
from train import parse_args, train


def worker(rank, world_size, args, uri):
    train(args, rank=rank, world_size=world_size, device='cpu', init_method=uri)


def main():
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix='d1-ddp-') as directory:
        path = Path(directory).resolve() / 'rendezvous'
        if path.exists():
            raise RuntimeError('rendezvous path already exists')
        mp.spawn(worker, args=(2, args, path.as_uri()), nprocs=2, join=True)
        if path.exists():
            path.unlink()


if __name__ == '__main__':
    main()
