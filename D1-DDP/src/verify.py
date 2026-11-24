import contextlib, tempfile
from pathlib import Path
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
from torchvision.models import resnet18


def worker(rank, uri):
    torch.set_num_threads(1)
    dist.init_process_group('gloo', init_method=uri, rank=rank, world_size=2)
    try:
        torch.manual_seed(42)
        base = resnet18(num_classes=10, norm_layer=lambda c: torch.nn.GroupNorm(32,c))
        initial = {k:v.clone() for k,v in base.state_dict().items()}
        generator = torch.Generator().manual_seed(100 + rank)
        inputs = [(torch.randn(1,3,32,32,generator=generator), torch.randint(0,10,(1,),generator=generator)) for _ in range(4)]
        grads=[]; params=[]
        for strategy in ('normal','delayed'):
            base.load_state_dict(initial); model=DDP(base); opt=torch.optim.SGD(model.parameters(),lr=.01,momentum=.9)
            opt.zero_grad(set_to_none=True)
            for i,(x,y) in enumerate(inputs):
                with model.no_sync() if strategy == 'delayed' and i < 3 else contextlib.nullcontext():
                    loss=torch.nn.functional.cross_entropy(model(x),y)/4
                    if not torch.isfinite(loss): raise RuntimeError('nonfinite loss')
                    loss.backward()
            grads.append([p.grad.detach().clone() for p in base.parameters()]); opt.step()
            params.append([p.detach().clone() for p in base.parameters()])
        errors=[]
        for left,right in zip(grads[0],grads[1]):
            torch.testing.assert_close(left,right,rtol=1e-4,atol=2e-6); errors.append((left-right).abs().max().item())
        perrors=[]
        for left,right in zip(params[0],params[1]):
            torch.testing.assert_close(left,right,rtol=1e-4,atol=2e-6); perrors.append((left-right).abs().max().item())
            ref=right.clone(); dist.broadcast(ref,0); torch.testing.assert_close(right,ref,rtol=0,atol=0)
        # One reference batch contains the exact samples processed by both ranks.
        local_x = torch.cat([x for x,y in inputs]); local_y = torch.cat([y for x,y in inputs])
        all_x = [torch.empty_like(local_x) for _ in range(2)]; all_y = [torch.empty_like(local_y) for _ in range(2)]
        dist.all_gather(all_x,local_x); dist.all_gather(all_y,local_y)
        ref_error = torch.zeros(())
        if rank == 0:
            ref = resnet18(num_classes=10, norm_layer=lambda c: torch.nn.GroupNorm(32,c))
            ref.load_state_dict(initial); ref_opt = torch.optim.SGD(ref.parameters(),lr=.01,momentum=.9)
            loss = torch.nn.functional.cross_entropy(ref(torch.cat(all_x)),torch.cat(all_y)); loss.backward(); ref_opt.step()
            for reference,actual in zip(ref.parameters(),params[1]):
                torch.testing.assert_close(reference,actual,rtol=1e-4,atol=2e-6)
                ref_error = torch.maximum(ref_error,(reference.detach()-actual).abs().max())
        dist.broadcast(ref_error,0)
        if rank==0: print(f'single vs DDP parameter max error={ref_error.item():.9g}',flush=True)
        if rank==0: print(f'PASS gradient max error={max(errors):.9g}; parameter max error={max(perrors):.9g}; rank max error=0',flush=True)
    finally: dist.destroy_process_group()


def main():
    with tempfile.TemporaryDirectory(prefix='d1-verify-') as directory:
        mp.spawn(worker,args=((Path(directory)/'store').resolve().as_uri(),),nprocs=2,join=True)

if __name__ == '__main__': main()
