---
layout: single
title: "PyTorch - The Training Loop and DDP, Animated (rank, world_size, batch_size)"
date: 2026-10-28 09:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - pytorch
  - python
  - ai
  - distributed
permalink: "2026/10/28/pytorch-training-loop-and-ddp-animated"
---

Based on [PyTorch in One Hour: From Tensors to Training Neural Networks on Multiple GPUs](https://sebastianraschka.com/teaching/pytorch-1h/) by Sebastian Raschka. This post skips tensors and autograd basics. It animates two things from the article: what happens to each batch on one GPU, and how Distributed Data Parallel (DDP) splits the same work across GPUs using `rank`, `world_size` and `batch_size`.

## One GPU: data → forward → loss → backward → step

This is the article's toy setup: 5 samples with 2 features each, an MLP of 752 parameters, `batch_size=2`, `shuffle=True`, `drop_last=True`, and SGD with `lr=0.5`. The batch orders, logits and losses come from running that code; the losses match the article's printed output (0.75, 0.65, 0.44, 0.13, 0.03, 0.00).

<iframe class="anim-frame" src="/assets/html/pytorch-single-gpu.html" title="PyTorch single-GPU training loop animation" style="width:100%;height:960px;border:1px solid #e8e8e8;border-radius:8px"></iframe>

What to watch for:

- **The loader owns the batch order.** `shuffle=True` reshuffles every epoch, and `drop_last=True` drops the fifth sample so an epoch never ends with a batch of 1. A different sample is dropped each epoch.
- **Forward builds the graph and backward consumes it.** `loss.backward()` fills `.grad` on every parameter, but only `optimizer.step()` changes the weights.
- **`zero_grad()` matters because `.grad` accumulates.** Since PyTorch 2.0, the default `set_to_none=True` sets the gradients to `None` instead of filling them with zeros.

## Many GPUs: DDP with rank, world_size and batch_size

With DDP, `torchrun` starts **one process per GPU**. Each process runs the same training loop shown above, with three changes:

```python
# torchrun --nproc_per_node=2 DDP-script-torchrun.py
rank = int(os.environ["LOCAL_RANK"])
world_size = int(os.environ["WORLD_SIZE"])
init_process_group(backend="nccl", rank=rank, world_size=world_size)
torch.cuda.set_device(rank)

# 1. each rank gets its own shard of the dataset
train_loader = DataLoader(train_ds, batch_size=2, shuffle=False,
                          drop_last=True, sampler=DistributedSampler(train_ds))
# 2. gradients are all-reduced across ranks during backward()
model = DDP(model.to(rank), device_ids=[rank])

for epoch in range(num_epochs):
    # 3. same shuffled order on every rank, different each epoch
    train_loader.sampler.set_epoch(epoch)
    for features, labels in train_loader:
        ...  # same forward / loss / zero_grad / backward / step as above

destroy_process_group()
```

Change `world_size`, the dataset size and `batch_size` to see how the shards, padding and steps per epoch change. Try `world_size=8` with 5 samples to hit the case where every loader is empty.

<iframe class="anim-frame" src="/assets/html/pytorch-ddp.html" title="PyTorch DDP animation: rank, world_size and batch_size" style="width:100%;height:1040px;border:1px solid #e8e8e8;border-radius:8px"></iframe>

### The arithmetic

| Quantity | Formula | 16 samples, `world_size=4`, `batch_size=2` |
|---|---|---|
| `world_size` | total processes (= GPUs) | 4 |
| `rank` | this process's ID, `0 … world_size-1`, which is also its GPU on one node | 0, 1, 2, 3 |
| samples per rank | `ceil(N / world_size)`, padded by repeating samples | 4 |
| rank `r`'s indices | `shuffled[r::world_size]` | rank 1 gets positions 1, 5, 9, 13 |
| per-GPU batch | `batch_size` passed to `DataLoader` | 2 |
| **global (effective) batch** | `batch_size × world_size` | **8** |
| steps per epoch | `samples_per_rank // batch_size` (`drop_last=True`) | 2 (vs. 8 on one GPU) |

`batch_size` in the `DataLoader` is **per GPU**, so going from 1 GPU to 4 multiplies the effective batch by 4 and divides the number of optimizer steps per epoch by 4. To keep the same effective batch, divide `batch_size` by `world_size`. To keep the same per-GPU batch, a common heuristic is to scale the learning rate along with the effective batch.

On more than one node, `torchrun` exports three numbers: `LOCAL_RANK` (the GPU index on this machine, used for `set_device`), `RANK` (the global ID, `node_rank × gpus_per_node + LOCAL_RANK`, used by the sampler), and `WORLD_SIZE` (`nodes × gpus_per_node`). On a single node, as in the article, `RANK == LOCAL_RANK`.

### Checking that all-reduce averages

I ran the DDP version with `torchrun --nproc_per_node=2` (gloo backend on CPU, 16 samples, `batch_size=2`) and compared one gradient entry with a single process that sees all 4 samples at once:

```
rank 0/2 RANK=0 LOCAL_RANK=0 idx [12, 9]  local loss 0.5934 synced grad 0.000697
rank 1/2 RANK=1 LOCAL_RANK=1 idx [10, 6]  local loss 0.5830 synced grad 0.000697
single-process grad on all 4 samples [12, 9, 10, 6]            0.000697
```

The losses differ because each rank only sees its own batch. The gradients agree after `backward()`: DDP all-reduces and **averages** them across ranks, overlapping that with the backward pass. The result is the gradient of one batch of `batch_size × world_size` samples. Every rank then takes the same `optimizer.step()`, so the replicas never diverge. Parameters are broadcast from rank 0 only once, when `DDP(...)` wraps the model.

The indices match the sampler too: `torch.randperm(16)` with seed `0 + epoch` gives `[12, 10, 9, 6, …]`, and `[r::2]` assigns rank 0 positions 0, 2, … (12, 9) and rank 1 positions 1, 3, … (10, 6).

<script>
document.querySelectorAll('iframe.anim-frame').forEach(function (f) {
  function fit() { try { f.style.height = (f.contentDocument.body.offsetHeight + 4) + 'px'; } catch (e) {} }
  f.addEventListener('load', function () {
    fit();
    try { new ResizeObserver(fit).observe(f.contentDocument.body); } catch (e) {}
  });
});
</script>
