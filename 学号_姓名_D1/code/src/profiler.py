"""Run a separate profiler capture; never use these timings as benchmark results."""
import json, tempfile
from pathlib import Path
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
from torchvision.models import resnet18
import contextlib, argparse


def worker(rank, uri, strategy, output, k):
    torch.set_num_threads(1); dist.init_process_group('gloo',init_method=uri,rank=rank,world_size=2)
    try:
        torch.manual_seed(42); model=DDP(resnet18(num_classes=10,norm_layer=lambda c:torch.nn.GroupNorm(32,c)))
        x=torch.randn(1,3,32,32); y=torch.tensor([rank]); model.zero_grad(set_to_none=True)
        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
            for i in range(k):
                with model.no_sync() if strategy=='delayed' and i<k-1 else contextlib.nullcontext():
                    (torch.nn.functional.cross_entropy(model(x),y)/4).backward()
        if rank==0:
            Path(output).mkdir(parents=True,exist_ok=True)
            prof.export_chrome_trace(str(Path(output)/f'K{k}_{strategy}_trace.json'))
            events=[{'name':e.key,'count':e.count,'cpu_total_us':e.cpu_time_total} for e in prof.key_averages() if 'allreduce' in e.key.lower() or 'all_reduce' in e.key.lower()]
            (Path(output)/f'K{k}_{strategy}_communication.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
            print('communication events:',events,flush=True)
    finally: dist.destroy_process_group()


def main():
    p=argparse.ArgumentParser(); p.add_argument('--strategy',choices=['normal','delayed'],default='delayed'); p.add_argument('--output',default='results/profiler'); p.add_argument('--k',type=int,default=4); a=p.parse_args()
    if a.k < 1: p.error('k must be positive')
    with tempfile.TemporaryDirectory(prefix='d1-profile-') as d: mp.spawn(worker,args=((Path(d)/'store').resolve().as_uri(),a.strategy,a.output,a.k),nprocs=2,join=True)

if __name__=='__main__': main()
