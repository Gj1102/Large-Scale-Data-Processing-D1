import argparse, contextlib, csv, json, os, time, random
from pathlib import Path
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler
from torchvision import datasets, transforms, models


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--data', default='./data'); p.add_argument('--output', default='results')
    p.add_argument('--experiment-id', default='trial'); p.add_argument('--batch', type=int, default=16)
    p.add_argument('--accum-steps', type=int, default=4); p.add_argument('--steps', type=int, default=200)
    p.add_argument('--warmup', type=int, default=20); p.add_argument('--seed', type=int, default=42)
    p.add_argument('--strategy', choices=['normal','delayed'], default='delayed')
    p.add_argument('--lr', type=float, default=0.01); p.add_argument('--workers', type=int, default=0)
    p.add_argument('--evaluate', action='store_true'); p.add_argument('--check-ranks', action='store_true'); p.add_argument('--download', action='store_true'); p.add_argument('--fake-data', action='store_true')
    a = p.parse_args()
    if min(a.batch,a.accum_steps,a.steps) < 1 or a.warmup < 0: p.error('invalid step or batch count')
    return a

def train(a, rank=None, world_size=None, device=None, init_method=None):
    world = int(os.environ.get('WORLD_SIZE','1')) if world_size is None else world_size
    rank = int(os.environ.get('RANK','0')) if rank is None else rank
    local = int(os.environ.get('LOCAL_RANK','0')) if device is None else rank
    device = torch.device(device) if device is not None else torch.device('cuda', local) if torch.cuda.is_available() else torch.device('cpu')
    cuda = device.type == 'cuda'
    if cuda: torch.cuda.set_device(device)
    if world > 1: dist.init_process_group('nccl' if cuda and os.name != 'nt' else 'gloo', init_method=init_method or 'env://', rank=rank, world_size=world)
    try:
        random.seed(a.seed); torch.manual_seed(a.seed)
        if cuda: torch.cuda.manual_seed_all(a.seed)
        norm = lambda channels: torch.nn.GroupNorm(32, channels)
        model = models.resnet18(num_classes=10, norm_layer=norm).to(device)
        if world > 1: model = DDP(model, device_ids=[local] if cuda else None)
        transform = transforms.ToTensor()
        if not a.fake_data and a.download and world > 1:
            if rank == 0: datasets.CIFAR10(a.data, train=True, download=True)
            dist.barrier()
        dataset = datasets.FakeData(size=50000, image_size=(3,32,32), num_classes=10, transform=transform) if a.fake_data else datasets.CIFAR10(a.data, train=True, download=a.download and world == 1, transform=transform)
        sampler = DistributedSampler(dataset, num_replicas=world, rank=rank, seed=a.seed, drop_last=True)
        loader = DataLoader(dataset, batch_size=a.batch, sampler=sampler, shuffle=sampler is None, drop_last=True, num_workers=a.workers)
        epoch = 0; iterator = iter(loader)
        opt = torch.optim.SGD(model.parameters(), lr=a.lr, momentum=0.9)
        rows=[]
        for step in range(a.warmup+a.steps):
            if cuda: torch.cuda.synchronize()
            start = time.perf_counter(); opt.zero_grad(set_to_none=True); loss_sum = torch.zeros((),device=device)
            micro_ms = forward_ms = backward_ms = 0.0
            for micro in range(a.accum_steps):
                try: x,y = next(iterator)
                except StopIteration:
                    epoch += 1
                    if sampler: sampler.set_epoch(epoch)
                    iterator=iter(loader); x,y=next(iterator)
                micro_start=time.perf_counter(); x,y=x.to(device),y.to(device)
                ctx = model.no_sync() if world > 1 and a.strategy == 'delayed' and micro < a.accum_steps-1 else contextlib.nullcontext()
                with ctx:
                    if cuda: torch.cuda.synchronize()
                    t=time.perf_counter(); loss = torch.nn.functional.cross_entropy(model(x),y)
                    if cuda: torch.cuda.synchronize()
                    forward_ms += (time.perf_counter()-t)*1000
                    t=time.perf_counter(); (loss/a.accum_steps).backward()
                    if cuda: torch.cuda.synchronize()
                    backward_ms += (time.perf_counter()-t)*1000
                loss_sum += loss.detach()/a.accum_steps
                micro_ms += (time.perf_counter()-micro_start)*1000
            t=time.perf_counter(); opt.step()
            if cuda: torch.cuda.synchronize()
            optimizer_ms=(time.perf_counter()-t)*1000
            if cuda: torch.cuda.synchronize()
            elapsed = torch.tensor(time.perf_counter()-start, device=device, dtype=torch.float64)
            if world > 1:
                dist.all_reduce(elapsed, op=dist.ReduceOp.MAX); dist.all_reduce(loss_sum); loss_sum /= world
            if not torch.isfinite(loss_sum): raise RuntimeError('non-finite loss')
            if step >= a.warmup and rank == 0:
                sec=elapsed.item(); effective=world*a.batch*a.accum_steps
                rows.append(dict(experiment_id=a.experiment_id, mode='ddp' if world>1 else 'single', world_size=world, micro_batch=a.batch, accum_steps=a.accum_steps, effective_batch=effective, sync_strategy=a.strategy, seed=a.seed, update_step=step-a.warmup+1, update_time_ms=sec*1000, micro_mean_ms=micro_ms/a.accum_steps, forward_mean_ms=forward_ms/a.accum_steps, backward_mean_ms=backward_ms/a.accum_steps, optimizer_ms=optimizer_ms, timing_rank=0, gradient_sync_backwards=a.accum_steps if a.strategy=='normal' and world>1 else (1 if world>1 else 0), throughput=effective/sec, loss=loss_sum.item()))
                print(f"update {step-a.warmup+1}: {sec*1000:.2f} ms loss={loss_sum.item():.4f}", flush=True)
        if a.evaluate and rank == 0:
            if a.fake_data: raise ValueError('evaluation requires CIFAR-10')
            test_data = datasets.CIFAR10(a.data, train=False, download=False, transform=transform)
            test_loader = DataLoader(test_data, batch_size=128, shuffle=False, num_workers=a.workers)
            eval_model = model.module if world > 1 else model
            eval_model.eval(); correct = 0; total_eval = 0
            with torch.no_grad():
                for x, y in test_loader:
                    x, y = x.to(device), y.to(device)
                    correct += (eval_model(x).argmax(dim=1) == y).sum().item(); total_eval += y.numel()
            out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
            (out / (a.experiment_id + '_evaluation.json')).write_text(json.dumps({'correct':correct, 'total':total_eval, 'accuracy':correct/total_eval}, indent=2), encoding='utf-8')
            print(f'test accuracy: {correct}/{total_eval} = {correct/total_eval:.4f}', flush=True)
        if a.check_ranks and world > 1:
            max_error = torch.zeros((), device=device)
            for parameter in model.parameters():
                reference = parameter.detach().clone()
                dist.broadcast(reference, src=0)
                max_error = torch.maximum(max_error, (parameter.detach() - reference).abs().max())
            dist.all_reduce(max_error, op=dist.ReduceOp.MAX)
            if rank == 0: print(f'rank parameter max error: {max_error.item():.9g}', flush=True)
            if max_error.item() > 1e-6: raise RuntimeError('rank parameters differ')
        if rank == 0:
            out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
            with (out/(a.experiment_id+'.csv')).open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
            times=torch.tensor([r['update_time_ms'] for r in rows]); total=sum(r['update_time_ms'] for r in rows)/1000
            summary={'mean_ms':times.mean().item(),'p50_ms':torch.quantile(times,.5).item(),'p95_ms':torch.quantile(times,.95).item(),'throughput':len(rows)*rows[0]['effective_batch']/total,'updates':len(rows)}
            (out/(a.experiment_id+'.json')).write_text(json.dumps(summary,indent=2),encoding='utf-8')
    finally:
        if world > 1 and dist.is_initialized(): dist.destroy_process_group()

if __name__ == '__main__': train(parse_args())
