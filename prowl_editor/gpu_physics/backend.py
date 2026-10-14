"""Where the SPIR-V kernels run.

A Backend owns buffers and runs compiled kernels over them. Two exist:

  InterpBackend   Crust's reference SPIR-V interpreter (tools/spirv_interp.py).
                  Pure Python: no GPU, no driver, slow (hundreds of particles,
                  not millions), but it executes the exact module that a GPU
                  would and refuses undefined behaviour. What the tests use,
                  and the fallback when there is no GPU.
  WgpuBackend     wgpu-py (pip install wgpu): Vulkan / Metal / DX12. Needs the
                  kernels built with scalar parameters in a storage buffer
                  (build.py --push-buffer), which is how the files in gpu/spirv
                  are built, so no push-constant device feature is required.

Both take the same calls, so GpuWorld does not know which it has:

    b = make_backend("auto")                  # wgpu if a GPU is there, else interp
    buf = b.alloc(4096)                       # bytes, zero filled
    b.write(buf, data, offset=0)
    prog = b.load(spv_bytes)                  # a module; prog.iface[entry] is its interface
    b.dispatch(prog, "entry", (groups, 1, 1), {binding: buf, ...}, params=bytes)
    b.dispatch_indirect(prog, "entry", args_buf, bindings, params)
    b.copy(src, dst, nbytes)
    data = b.read(buf)                        # waits for everything queued before it

Kernels are listed by the binding numbers the SPIR-V uses; a module built in
push-buffer mode names its parameter block in iface["push_binding"], and the
`params` bytes handed to dispatch() are what goes there.
"""
import os
import struct
import sys

PARAMS_SLOT = 256            # bytes per queued dispatch's parameters (storage-offset alignment)
PARAMS_SLOTS = 8192          # dispatches per frame before the ring wraps (flushes first)


class BackendError(RuntimeError):
    pass


class Buf:
    """A buffer a backend made. Treat as opaque."""
    __slots__ = ("nbytes", "data", "gpu", "indirect")

    def __init__(self, nbytes, data=None, gpu=None, indirect=False):
        self.nbytes = nbytes
        self.data = data
        self.gpu = gpu
        self.indirect = indirect


class Program:
    """A loaded SPIR-V module: its words/bytes and the interface of each entry point."""

    def __init__(self, spv, iface):
        self.spv = spv
        self.iface = {e["name"]: e for e in iface}
        self.handle = None


def _describe(spv):
    from . import crust_path
    crust_path.ensure()
    from shivyc import spirv_reader
    from shivyc.spirv import bytes_to_words
    words = bytes_to_words(spv)
    return words, spirv_reader.describe(words)


class Backend:
    name = "?"

    def alloc(self, nbytes, data=None, indirect=False):
        raise NotImplementedError

    def write(self, buf, data, offset=0):
        raise NotImplementedError

    def read(self, buf, offset=0, nbytes=None):
        raise NotImplementedError

    def load(self, spv):
        raise NotImplementedError

    def dispatch(self, prog, entry, groups, bindings, params=b""):
        raise NotImplementedError

    def dispatch_indirect(self, prog, entry, args, bindings, params=b""):
        raise NotImplementedError

    def copy(self, src, dst, nbytes, src_off=0, dst_off=0):
        raise NotImplementedError

    def flush(self):
        pass

    def close(self):
        pass


class InterpBackend(Backend):
    name = "interp"

    def __init__(self):
        from . import crust_path
        crust_path.ensure()
        import spirv_interp
        self._interp = spirv_interp
        self.dispatches = 0

    def alloc(self, nbytes, data=None, indirect=False):
        b = Buf(nbytes, bytearray(nbytes), indirect=indirect)
        if data is not None:
            b.data[:len(data)] = data
        return b

    def write(self, buf, data, offset=0):
        buf.data[offset:offset + len(data)] = data

    def read(self, buf, offset=0, nbytes=None):
        n = buf.nbytes - offset if nbytes is None else nbytes
        return bytes(buf.data[offset:offset + n])

    def load(self, spv):
        words, iface = _describe(spv)
        prog = Program(spv, iface)
        prog.handle = self._interp.Machine(words)
        return prog

    def _run(self, prog, entry, groups, bindings, params):
        info = prog.iface[entry]
        arrays = {}
        for binding, buf in bindings.items():
            arrays[binding] = buf.data
        push = b""
        pb = info.get("push_binding")
        if pb is not None:
            arrays[pb["binding"]] = bytearray(params)
        else:
            push = params
        prog.handle.run(entry, tuple(groups), arrays, push)
        self.dispatches += 1

    def dispatch(self, prog, entry, groups, bindings, params=b""):
        if min(groups) > 0:
            self._run(prog, entry, groups, bindings, params)

    def dispatch_indirect(self, prog, entry, args, bindings, params=b""):
        gx, gy, gz = struct.unpack_from("<3I", args.data, 0)
        self.dispatch(prog, entry, (gx, gy, gz), bindings, params)

    def copy(self, src, dst, nbytes, src_off=0, dst_off=0):
        dst.data[dst_off:dst_off + nbytes] = src.data[src_off:src_off + nbytes]


class WgpuBackend(Backend):
    """wgpu-py. Written against wgpu 0.32 (pip install wgpu==0.32.0).

    Every dispatch is its own compute pass in one command encoder, so passes
    run in order with their writes visible to the next. A dispatch's parameters
    go in a 256-byte slot of one big buffer, bound with an offset: queue
    writes all land before the submit, so each dispatch needs its own slot."""
    name = "wgpu"

    def __init__(self, power_preference="high-performance"):
        try:
            import wgpu
        except ImportError as e:
            raise BackendError("wgpu is not installed (pip install wgpu): %s" % e)
        self.wgpu = wgpu
        try:
            adapter = wgpu.gpu.request_adapter_sync(power_preference=power_preference)
        except Exception as e:
            raise BackendError("no GPU adapter: %s" % e)
        if adapter is None:
            raise BackendError("no GPU adapter")
        limits = {}
        try:
            have = adapter.limits
            limits = {"max-storage-buffers-per-shader-stage": min(16, have.get("max-storage-buffers-per-shader-stage", 8)),
                      "max-storage-buffer-binding-size": have.get("max-storage-buffer-binding-size", 134217728),
                      "max-buffer-size": have.get("max-buffer-size", 268435456)}
        except Exception:
            limits = {}
        try:
            self.device = adapter.request_device_sync(required_limits=limits)
        except Exception as e:
            raise BackendError("cannot open the GPU device: %s" % e)
        self.adapter_info = getattr(adapter, "info", {})
        self.queue = self.device.queue
        self._enc = None
        self._slot = 0
        self._params = self.device.create_buffer(
            size=PARAMS_SLOT * PARAMS_SLOTS,
            usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST)
        self._zero = bytes(PARAMS_SLOT)
        self._layouts = {}
        self.dispatches = 0

    # -- buffers
    def alloc(self, nbytes, data=None, indirect=False):
        wgpu = self.wgpu
        usage = (wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC
                 | wgpu.BufferUsage.COPY_DST)
        if indirect:
            usage |= wgpu.BufferUsage.INDIRECT
        size = max(16, (nbytes + 3) & ~3)
        g = self.device.create_buffer(size=size, usage=usage)
        b = Buf(nbytes, gpu=g, indirect=indirect)
        self.queue.write_buffer(g, 0, bytes(size) if data is None else
                                bytes(data) + bytes(size - len(data)))
        return b

    def write(self, buf, data, offset=0):
        self.flush()
        data = bytes(data)
        pad = (-len(data)) % 4
        self.queue.write_buffer(buf.gpu, offset, data + bytes(pad))

    def read(self, buf, offset=0, nbytes=None):
        self.flush()
        n = buf.nbytes - offset if nbytes is None else nbytes
        return bytes(self.queue.read_buffer(buf.gpu, offset, (n + 3) & ~3))[:n]

    def copy(self, src, dst, nbytes, src_off=0, dst_off=0):
        enc = self._encoder()
        enc.copy_buffer_to_buffer(src.gpu, src_off, dst.gpu, dst_off, (nbytes + 3) & ~3)

    # -- programs
    def load(self, spv):
        _words, iface = _describe(spv)
        prog = Program(spv, iface)
        prog.handle = self.device.create_shader_module(code=bytes(spv))
        return prog

    def _pipeline(self, prog, entry):
        key = (id(prog), entry)
        hit = self._layouts.get(key)
        if hit is not None:
            return hit
        wgpu = self.wgpu
        info = prog.iface[entry]
        entries = []
        for b in info["buffers"]:
            ro = b["access"] == "read"
            entries.append({
                "binding": b["binding"],
                "visibility": wgpu.ShaderStage.COMPUTE,
                "buffer": {"type": wgpu.BufferBindingType.read_only_storage if ro
                           else wgpu.BufferBindingType.storage}})
        pb = info.get("push_binding")
        if pb is not None:
            entries.append({
                "binding": pb["binding"],
                "visibility": wgpu.ShaderStage.COMPUTE,
                "buffer": {"type": wgpu.BufferBindingType.read_only_storage,
                           "has_dynamic_offset": False}})
        elif info.get("push_size"):
            raise BackendError("%s uses push constants; build the kernels with "
                               "--push-buffer for the wgpu backend" % entry)
        bgl = self.device.create_bind_group_layout(entries=entries)
        layout = self.device.create_pipeline_layout(bind_group_layouts=[bgl])
        pipe = self.device.create_compute_pipeline(
            layout=layout, compute={"module": prog.handle, "entry_point": entry})
        self._layouts[key] = (pipe, bgl, info)
        return self._layouts[key]

    # -- dispatch
    def _encoder(self):
        if self._enc is None:
            self._enc = self.device.create_command_encoder()
            self._slot = 0
        return self._enc

    def flush(self):
        if self._enc is not None:
            self.queue.submit([self._enc.finish()])
            self._enc = None
            self._slot = 0

    def _bind(self, prog, entry, bindings, params):
        pipe, bgl, info = self._pipeline(prog, entry)
        if self._slot >= PARAMS_SLOTS:
            self.flush()
        enc = self._encoder()
        entries = []
        for b in info["buffers"]:
            buf = bindings.get(b["binding"])
            if buf is None:
                raise BackendError("%s: nothing bound at binding %d (%s)" % (entry, b["binding"], b["name"]))
            entries.append({"binding": b["binding"],
                            "resource": {"buffer": buf.gpu, "offset": 0, "size": buf.gpu.size}})
        pb = info.get("push_binding")
        if pb is not None:
            if len(params) > PARAMS_SLOT:
                raise BackendError("%s: %d bytes of parameters" % (entry, len(params)))
            off = self._slot * PARAMS_SLOT
            self._slot += 1
            padded = bytes(params) + bytes(max(16, (len(params) + 3) & ~3) - len(params))
            self.queue.write_buffer(self._params, off, padded)
            entries.append({"binding": pb["binding"],
                            "resource": {"buffer": self._params, "offset": off,
                                         "size": len(padded)}})
        group = self.device.create_bind_group(layout=bgl, entries=entries)
        return enc, pipe, group

    def dispatch(self, prog, entry, groups, bindings, params=b""):
        if min(groups) <= 0:
            return
        enc, pipe, group = self._bind(prog, entry, bindings, params)
        cp = enc.begin_compute_pass()
        cp.set_pipeline(pipe)
        cp.set_bind_group(0, group)
        cp.dispatch_workgroups(*[int(g) for g in groups])
        cp.end()
        self.dispatches += 1

    def dispatch_indirect(self, prog, entry, args, bindings, params=b""):
        enc, pipe, group = self._bind(prog, entry, bindings, params)
        cp = enc.begin_compute_pass()
        cp.set_pipeline(pipe)
        cp.set_bind_group(0, group)
        cp.dispatch_workgroups_indirect(args.gpu, 0)
        cp.end()
        self.dispatches += 1

    def close(self):
        self.flush()


def make_backend(kind="auto"):
    """'interp', 'wgpu', or 'auto' (wgpu when a GPU can be opened, else interp)."""
    kind = (kind or "auto").lower()
    if kind == "interp":
        return InterpBackend()
    if kind == "wgpu":
        return WgpuBackend()
    if kind != "auto":
        raise BackendError("unknown GPU backend %r (interp, wgpu, auto)" % kind)
    try:
        return WgpuBackend()
    except BackendError:
        return InterpBackend()
