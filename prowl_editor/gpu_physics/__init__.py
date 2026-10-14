"""GPU physics for Prowl2D: the circle / particle engine of crustos/gpu-physics-engine,
its kernels compiled by Crust to SPIR-V, run through wgpu (or Crust's interpreter)."""
from .backend import make_backend, BackendError, InterpBackend, WgpuBackend   # noqa: F401
from .gpuinput import GpuInput                                                # noqa: F401
from .world import GpuWorld                                                   # noqa: F401
