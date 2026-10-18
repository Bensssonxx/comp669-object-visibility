from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F


class FrozenEncoder:
    """Official weights, shared mean-of-final-patch pooling, L2-normalized features."""
    def __init__(self, root: Path, name: str, device: str = "mps"):
        self.name = name
        self.device = torch.device(device)
        if device == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError("MPS unavailable. Use a GPU-enabled execution context or explicitly set cpu.")
        torch.set_num_threads(4)
        if name == "aimv2":
            from aim.v2.utils import _load_torch
            self.model = _load_torch("aimv2-large-patch14-224", str(root / "models/aimv2-large-patch14-224.safetensors"))
        elif name == "dinov2":
            os.environ["XFORMERS_DISABLED"] = "1"
            sys.path.insert(0, str(root / "vendor/dinov2"))
            from dinov2.hub.backbones import dinov2_vitl14
            self.model = dinov2_vitl14(pretrained=False)
            state = torch.load(root / "models/dinov2_vitl14_pretrain.pth", map_location="cpu", weights_only=True)
            self.model.load_state_dict(state, strict=True)
            del state
        else:
            raise ValueError(name)
        self.model.eval().requires_grad_(False).to(self.device)
        self.mean = torch.tensor([0.485, 0.456, 0.406], device=self.device)[None, :, None, None]
        self.std = torch.tensor([0.229, 0.224, 0.225], device=self.device)[None, :, None, None]

    @torch.inference_mode()
    def encode(self, rgb: np.ndarray) -> np.ndarray:
        x = torch.from_numpy(rgb.copy()).permute(0, 3, 1, 2).to(self.device, dtype=torch.float32) / 255
        x = (x - self.mean) / self.std
        if self.name == "aimv2":
            patches = self.model(x)
        else:
            patches = self.model.forward_features(x)["x_norm_patchtokens"]
        if patches.ndim != 3 or patches.shape[1:] != (256, 1024):
            raise ValueError(f"Unexpected last-patch feature shape: {patches.shape}")
        return F.normalize(patches.mean(dim=1), dim=1).cpu().numpy()

    def benchmark(self, batch_size=4):
        rng = np.random.default_rng(0)
        x = rng.integers(0, 256, (batch_size, 224, 224, 3), dtype=np.uint8)
        self.encode(x)
        start = time.monotonic()
        y = self.encode(x)
        return {"images_per_second": batch_size / (time.monotonic() - start), "shape": list(y.shape),
                "all_finite": bool(np.isfinite(y).all()), "feature_norm": float(np.linalg.norm(y, axis=1).mean())}
