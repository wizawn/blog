---
title: "在 16G 无显卡机器上跑通 MOSS-TTSD 的折腾记录"
date: 2026-04-17T05:00:00+08:00
draft: false
categories: ["AI 部署"]
tags: ["MOSS-TTSD", "语音合成", "量化", "Swap", "Debian"]
description: "记录在 6 核 16G 无 GPU 的 Debian 11 服务器上跑通开源对话语音合成模型 OpenMOSS/MOSS-TTSD 的完整过程：为什么默认 CPU 模式会把 16.7GB 权重翻倍撑爆内存，以及如何靠 Swap、bfloat16 或 4-bit 量化与 SSH 隧道稳住服务。"
weight: 10
---

[`OpenMOSS/MOSS-TTSD`](https://github.com/OpenMOSS/MOSS-TTSD) 这套开源对话语音合成模型的音色还原度相当惊艳（社区里常能看到的 `Aionara/MOSS-TTSD` 其实是它的个人 Fork，拉代码直接认准官方主仓就行），但它对无显卡小鸡实在不太友好：单是 `bfloat16` 半精度的模型权重就有 16.7GB。我手头那台 6 核 16G 内存、没配独显的 Debian 11 云服务器，拉下代码直接跑必吃内核 OOM Killer，终端冷冰冰蹦出一句 `Killed` 就没影了。

更坑的地方在代码里。去翻它的 `gradio_demo.py` 第 120 行附近就能发现，官方脚本检测到机器没有 CUDA、退回 CPU 跑推理时，默认把加载精度改成了 `torch.float32`。这意味着原本 16.7GB 的权重一进内存直接翻倍膨胀到三十多 GB，16G 物理内存神仙也扛不住。

折腾了一番，靠"划 16G Swap 垫底 + 压住 CPU 加载精度（`bfloat16` 或 NF4 4-bit 量化）+ 锁死本地回环监听"三步组合，把常驻物理内存压到了 7G 到 9G 左右，总算在这台无卡机器上稳稳跑通了。趁热乎把完整过程和原版脚本里的几个暗坑记一笔。

## 0x00 先划 16G Swap 兜底，别在跑着模型时强卸交换文件

哪怕后面上了半精度或 4-bit 量化，`from_pretrained` 在流式读取权重分片并转换格式的峰值阶段依然要吃不少周转空间，16G 物理内存卡在生死线上太悬了。第一步先把编译工具和音频处理必用的 `ffmpeg` 装上，再划一个 16G 的 `/swapfile` 垫底（硬盘最好留出 50GB 以上余量放 Hugging Face 权重缓存和交换文件）：

```bash
sudo apt update && sudo apt install -y git wget ffmpeg build-essential

sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

free -h
```

看到 `Swap` 那一行显示 `16Gi` 就妥了。顺手提个醒：万一后面你觉得 16G Swap 还是紧巴巴、想扩到 24G，动手敲 `sudo swapoff /swapfile` 之前一定先把正在跑的 Python 模型进程停掉，看 `free -h` 确认 Swap 占用退干净了再卸，接着重新跑一遍 `sudo fallocate -l 24G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`。内存本来就满着的时候硬卸 Swap，机器当场就会 OOM 卡死。

## 0x01 用 Miniforge 配 Python 3.10 与纯 CPU 版 PyTorch

Debian 11 自带的系统 Python 还是 `3.9`，而 `MOSS-TTSD` 源码里到处都在用 Python 3.10 才引入的 `X | Y` 联合类型注解，拿 3.9 一跑直接抛 `TypeError: unsupported operand type(s) for |`。

装独立 Python 环境时，现在更推荐直接用社区维护的 Miniforge（默认走 `conda-forge` 通道，不会像 2025 年年中之后的官方 Miniconda 那样在非交互终端里突然甩出 `CondaToSNonInteractiveError` 逼你手动同意 Anaconda 商业条款）：

```bash
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b -p "$HOME/miniforge3"
source "$HOME/miniforge3/bin/activate"

conda create -n moss python=3.10 -y
conda activate moss
```

要是你机器上本来就装着 Miniconda 撞上了那个条款报错，敲两句 `conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main` 和 `.../pkgs/r` 也能放行。

激活 `moss` 环境后，切记先单独装纯 CPU 版的 PyTorch（省得默认 `pip` 给你拉好几个 G 根本用不上的 CUDA 动态库占满小鸡硬盘），然后再克隆官方仓库装项目自身的 `requirements.txt`（不少二手教程漏了克隆仓库和装 `requirements.txt` 这步，光装几个零散包根本跑不起来）：

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

mkdir -p ~/apps && cd ~/apps
git clone https://github.com/OpenMOSS/MOSS-TTSD.git
cd MOSS-TTSD

pip install -r requirements.txt
pip install accelerate bitsandbytes torchao
```

第一次拉起服务时，程序会自动从 Hugging Face 下载主模型和音频编解码器（Codec）权重（也可通过 `--model_path`、`--codec_path` 指定本地提前下好的目录）；国内机器拉权重慢的话可以先 `export HF_ENDPOINT=https://hf-mirror.com`。

## 0x02 改 `gradio_demo.py`：管住 CPU 下的 `float32` 翻倍膨胀

打开仓库里的 `gradio_demo.py` 翻到第 120 到 145 行附近，能看到原版代码先拼了一个包含 `trust_remote_code=True`、`torch_dtype` 和 `attn_implementation` 的 `model_kwargs` 字典（CPU 分支里默认塞的是 `torch.float32`），最后在第 143 行调：

```python
model = AutoModel.from_pretrained(model_path, **model_kwargs).to(device)
```

在无 GPU 服务器上给它"瘦身"有两条实在路子，按手头机器情况二选一就行。

第一条路兼容性最省事：把 `gradio_demo.py` 第 120 行那句三元判断直接改成固定 `dtype = torch.bfloat16`。光改这一处，就能把原本膨胀到三十多 G 的权重砍回 16.7GB 原尺寸，配合前面划好的 16G Swap 可以顺利加载起来，完全不挑 `bitsandbytes` 编译环境；不过因为 16.7GB 权重在 16G 物理内存机器上仍有一截要落进磁盘 Swap（且不含 AVX512_BF16/AMX 加速的普通 CPU 跑 bf16 靠软件模拟），每次推理免不了频繁换页拖慢速度，想把常驻物理内存真正压到 7G - 9G 还得走下面的第二条路。

第二条路压内存压得更狠：引入 `BitsAndBytesConfig` 做 NF4 4-bit 量化。这里有两个细节千万别抄错老教程：一是早年的 `bitsandbytes` 强依赖 CUDA，没显卡一跑就报 `No GPU found`，必须确保刚才 `pip` 装上的是带 CPU 后端支持的新版 `bitsandbytes` 和 `transformers`；二是在纯 CPU 上算力类型别设成 `torch.float16`（x86 CPU 原生算 fp16 极慢甚至缺指令支持），设成 `torch.bfloat16` 才对路。改的时候把 `model_kwargs["torch_dtype"]` 也显式设为 `torch.bfloat16`（确保未被 4-bit 量化的 Embedding 等模块维持 bf16 而不退回 fp32），并把尾巴上的 `.to(device)` 去掉：

```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4",
)

model_kwargs["torch_dtype"] = torch.bfloat16
model = AutoModel.from_pretrained(
    model_path,
    quantization_config=bnb_config,
    device_map="cpu",
    **model_kwargs,
)
```

说句实话，4-bit 量化并不是把整个模型一刀切缩成四分之一：它主要压的是线性层（`nn.Linear`）权重（相对 bf16 约省四倍、相对原来默认的 fp32 约省八倍），而词表 Embedding、LayerNorm 和独立的音频 Codec 依然保持 `bfloat16` 半精度。实测跑稳定之后，物理内存常驻在 7G 到 9G 上下，加载峰值期会借用 2G 到 4G 的 Swap。每次点生成语音时 6 个 CPU 核会瞬间飙满 100%，出音频肯定比显卡慢一截，但合成出来的对话语气和音质完全没缩水。

## 0x03 锁死回环监听与 `systemd` 的 `PATH` 暗坑

到了启动这一步，网上不少帖子教人敲 `export GRADIO_SERVER_NAME="0.0.0.0"` 再去防火墙开 `7863` 端口对全网放行。这么配其实一脚踩进了两个坑里。

头一个坑是环境变量根本没生效：`gradio_demo.py` 调 `demo.launch(server_name=args.host, ...)` 时显式传了命令行参数 `--host`，`GRADIO_SERVER_NAME` 被直接盖掉了，而且更要命的是 `--host` 在源码里的默认值本来就是 `0.0.0.0`（什么参数都不传照样对全网敞开；唯有 `share=False` 默认不传 `--share` 不会生成 `gradio.live` 外网链接）。

第二个坑要命得多：这是一个带零样本声音克隆能力的 Web 面板，而且默认连个登录密码框都没有！一旦绑在 `0.0.0.0:7863` 敞给全网，轻则被路过的爬虫拿去白蹭算力把你 6 核 CPU 卡死，重则被人传一段录音上去克隆熟人声音搞电信诈骗，实名制云主机的责任全得你自己扛。

最干净利落的做法就是明确传 `--host 127.0.0.1` 和 `--device cpu`（省得默认 `cuda:0` 再报一次回退提示），只绑本机回环口，防火墙和云安全组连一个端口都不用开：

```bash
python gradio_demo.py --host 127.0.0.1 --port 7863 --device cpu
```

在自己电脑上用的时候，终端敲一行 SSH 本地端口转发隧道连上去：

```bash
ssh -N -L 7863:127.0.0.1:7863 user@你的服务器IP
```

本机浏览器直接打开 `http://127.0.0.1:7863` 就能用，外网扫描器连影儿都摸不着。

最后如果要把服务写成 `systemd` 单元常驻后台，千万留意 `Environment="PATH=..."` 那一行：别只写 Miniforge 虚拟环境那一个 `bin` 目录把系统原有的路径全顶掉了！一旦漏了 `/usr/bin`，Gradio 在切分和转码音频调系统 `/usr/bin/ffmpeg` 时会当场报找不到可执行文件。用普通用户身份跑的完整单元配置长这样：

```ini
# /etc/systemd/system/moss-ttsd.service
[Unit]
Description=MOSS-TTSD CPU Inference Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=你的普通用户名
WorkingDirectory=/home/你的普通用户名/apps/MOSS-TTSD
Environment="PATH=/home/你的普通用户名/miniforge3/envs/moss/bin:/usr/local/bin:/usr/bin:/bin"
# 国内服务器首次冷启动需拉取权重时可一并取消下行注释：
# Environment="HF_ENDPOINT=https://hf-mirror.com"
ExecStart=/home/你的普通用户名/miniforge3/envs/moss/bin/python gradio_demo.py --host 127.0.0.1 --port 7863 --device cpu
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

保存后跑 `sudo systemctl daemon-reload && sudo systemctl enable --now moss-ttsd`。纯 CPU 首次冷启动把十几个 G 的分片嚼进内存大约要等五到十分钟，挂着 `journalctl -u moss-ttsd -f` 看到打出 `Running on local URL: http://127.0.0.1:7863` 就大功告成了。更多量化参数细节可以对照 [Hugging Face BitsAndBytes 文档](https://huggingface.co/docs/transformers/main/en/quantization/bitsandbytes) 和 [Gradio 官方文档](https://gradio.app/docs/)。
