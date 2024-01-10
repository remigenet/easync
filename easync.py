import asyncio
from threading import Thread
import inspect
from concurrent.futures import TimeoutError, ProcessPoolExecutor
import functools

import time
import uuid


def ensure_async(func):
    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    return func if asyncio.iscoroutinefunction(func) or inspect.iscoroutinefunction(func) else wrapped

class SecondaryLoop:
    def __init__(self):
        self._loop = None
        self._executor = None
        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        self._loop.set_task_factory(asyncio.eager_task_factory)
        asyncio.set_event_loop(self._loop)
        self._executor = ProcessPoolExecutor()
        self._loop.run_forever()

    def get_loop(self):
        while not self._loop:
            pass  # Wait until the loop is set up
        return self

    def __getattr__(self, name):
        if name == '_executor':
            return self._executor
        return getattr(self._loop, name)

# Initialize the secondary loop
secondary_loop = SecondaryLoop()

RMETHODS = {'__add__': '__radd__', '__sub__': '__rsub__', '__mul__': '__rmul__', '__truediv__': '__rtruediv__', '__floordiv__': '__rfloordiv__',
             '__mod__': '__rmod__', '__pow__': '__rpow__', '__and__': '__rand__', '__or__': '__ror__', '__xor__': '__rxor__',
             '__lshift__': '__rlshift__', '__rshift__': '__rrshift__', '__matmul__': '__rmatmul__',
             '__radd__': '__add__', '__rsub__': '__sub__', '__rmul__': '__mul__', '__rtruediv__': '__truediv__', '__rfloordiv__': '__floordiv__',
             '__rmod__': '__mod__', '__rpow__': '__pow__', '__rand__': '__and__', '__ror__': '__or__', '__rxor__': '__xor__',
             '__rlshift__': '__lshift__', '__rrshift__': '__rshift__', '__rmatmul__': '__rmatmul__'}

AMETHODS = ["__add__", "__radd__", "__sub__", "__rsub__", "__mul__",  "__rmul__", "__matmul__", "__rmatmul__", "__truediv__", "__rtruediv__", "__floordiv__", "__rfloordiv__",
            "__mod__", '__rmod__', "__pow__", "__rpow__", "__abs__"]


def contains_awaitable(instance, cls):
    if isinstance(instance, cls):
        return True
    elif isinstance(instance, (list, tuple, set)):
        return any(contains_awaitable(arg, cls) for arg in instance)
    elif isinstance(instance, dict):
        return any(contains_awaitable(arg, cls) for arg in instance.values())
    else:
        return False

def any_apply(instance, lambda_select = lambda x: False, lambda_apply = lambda x: x):
    if lambda_select(instance):
        return lambda_apply(instance)
    elif isinstance(instance, (list, tuple, set)):
        return type(instance)(any_apply(elem, lambda_select = lambda_select, lambda_apply=lambda_apply) for elem in instance)
    elif isinstance(instance, dict):
        return {any_apply(key, lambda_select = lambda_select, lambda_apply=lambda_apply): any_apply(value, lambda_select = lambda_select, lambda_apply=lambda_apply) for key, value in instance.items()}
    else:
        return instance

class remawaitable:
    def __init__(self, func, *args, **kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._future = None
        self.__awaited = False
        self._id = uuid.uuid4()
        self._loop = secondary_loop.get_loop()
        if not contains_awaitable(args, remawaitable) and not contains_awaitable(kwargs, remawaitable):
            self._future = self._loop._loop.create_task(self._func(*self._args, **self._kwargs))
            #self._future = asyncio.run_coroutine_threadsafe(self._func(*self._args, **self._kwargs), self._loop._loop)
        
    @property
    def reresult(self):
        if not self.__awaited:
            self.__await__()
        return self.__result

    def __await__(self):
        if self._future is None:
            self._args, self._kwargs = any_apply((self._args, self._kwargs), lambda_select = lambda x: isinstance(x, remawaitable), lambda_apply = lambda x: x.reresult)
            self._future = self._loop._loop.create_task(self._func(*self._args, **self._kwargs))
            #self._future = asyncio.run_coroutine_threadsafe(self._func(*self._args, **self._kwargs), self._loop._loop)
        while self._future.done() is False:
            self._loop.call_soon_threadsafe(asyncio.sleep(0.001).send, None)
            pass
        self.__result = self._future.result()
        self.__awaited = True
        return self

    @classmethod
    def make_dunder(cls, method):
        @functools.wraps(method)
        def dunder(self, *args, **kwargs):
            args, kwargs = any_apply((args, kwargs), lambda_select = lambda x: isinstance(x, remawaitable), lambda_apply = lambda x: x.reresult)
            if isinstance(self, cls):
                self = self.reresult
            if not isinstance((res := self.__getattribute__(method)(*args, **kwargs)), NotImplemented.__class__):
                return res
            elif method in RMETHODS and (other:=args[0] if args else kwargs.get('other', None)) and (rm := getattr(other, RMETHODS.get(method))):
                return rm(self, *args[1:], **{k: v for k, v in kwargs.items() if k != 'other'})
        @functools.wraps(dunder)
        def lazy_dunder(self, *args, **kwargs):
            return remawaitable(ensure_async(dunder), self, *args, **kwargs)
        if method in AMETHODS:
            return lazy_dunder
        return dunder
        
    def __new__(cls, func, *args, **kwargs):
        common_dunder_methods = [
            "__add__", "__radd__", "__sub__", "__rsub__", "__mul__",  "__rmul__", "__matmul__", "__rmatmul__", "__truediv__", "__rtruediv__", "__floordiv__", "__rfloordiv__",
            "__mod__", '__rmod__', "__pow__", "__rpow__", "__abs__", "__and__", "__rand__", "__or__", "__ror__", "__xor__", "__rxor__",  
            "__lshit__", "__rlshift__", "__rshift__", "__rrshift__",
            "__lt__", "__le__", "__eq__",
            "__ne__", "__gt__", "__ge__", "__neg__", "__pos__",
            "__str__", "__repr__", "__bool__", "__hash__", '__getattr__', '__getitem__', '__setitem__', '__delitem__', '__contains__', '__iter__', '__next__', '__len__', '__call__', '__enter__', '__exit__'
        ]
        for method in common_dunder_methods:
            setattr(cls, method, cls.make_dunder(method))
        return super().__new__(cls)


def remasync(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return remawaitable(ensure_async(func), *args, **kwargs)
    return wrapper




# -ffast-math
# -fitodcallsbyclone -fnt-store=aggressive 
# -fomit-frame-pointer -fno-plt -pthread -fstack-protector-strong -fvisibility=hidden -falign-functions -fitodcallsbyclone -I/opt/rocm/include -fopenmp-extensions -fsplit-machine-functions -funsafe-math-optimizations -flto"
 
# git clean -fxd

# export PATH="/opt/rocm/llvm/alt/bin/llvm-*:$PATH:"
# export OPT="-O3 -march=native -mtune=native"
# export CC="/opt/rocm/llvm/alt/bin/clang"
# export CPP="/opt/rocm/llvm/alt/bin/clang-cpp" 
# export CXX="/opt/rocm/llvm/alt/bin/clang++" 
# export NM="/opt/rocm/llvm/alt/bin/llvm-nm"
# export RANLIB="/opt/rocm/llvm/alt/bin/llvm-ranlib"
# export PROFDATA="/opt/rocm/llvm/alt/bin/llvm-profdata"
# export PROFGEN="/opt/rocm/llvm/alt/bin/lvm-profgen"
# export nm="$NM"
# export ranlib="$RANLIB"
# export profdata="$PROFDATA"
# export profgen="$PROFGEN"
# export readelf="/opt/rocm/llvm/alt/bin/llvm-readelf"
# export ar="/opt/rocm/llvm/alt/bin/llvm-ar"
# export cc="$CC"
# export cxx="$CXX"
# export cpp="$CPP"
# export CFLAGS="-O3 -march=native -Wstrict-prototypes -Wprofile-instr-out-of-date -mtune=native -pthread -faligned-allocation -fstruct-layout=7 -fno-plt -fopenmp-extensions -fsplit-machine-functions -fopenmp-extensions -fsplit-machine-functions -pipe -fomit-frame-pointer -fno-plt -pthread -fstack-protector-strong -fvisibility=hidden -falign-functions -fitodcallsbyclone" 

# export CXXFLAGS="-O3 -march=native -mtune=native -fstruct-layout=7 -fno-plt -pthread -fvisibility=hidden -falign-functions -falign-jumps -falign-loops -falign-labels -fitodcallsbyclone -fopenmp-extensions -fsplit-machine-functions"  
# export LDFLAGS_NO_DIST="-O3 -march=native -mtune=native -flto"  
# export CFLAGS_NO_DIST="-O3 -march=native -mtune=native -fstruct-layout=7"

# export LIBPYTHON="/usr/lib/python3.12/dist-packages/:/usr/lib/python3/dist-packages/"
# export LDFLAGS="-L/opt/AMD/aocl/aocl-linux-aocc-4.1.0/aocc/lib -L/opt/amdgpu/lib/x86_64-linux-gnu"
# export WITH_LIBS="/opt/AMD/aocl/aocl-linux-aocc-4.1.0/aocc/lib/libblis.a /opt/AMD/aocl/aocl-linux-aocc-4.1.0/aocc/lib/libfftw3.a /opt/AMD/aocl/aocl-linux-aocc-4.1.0/aocc/lib/libamdlibm.a /opt/AMD/aocl/aocl-linux-aocc-4.1.0/aocc/lib/libscalapack.a /opt/amdgpu/lib/x86_64-linux-gnu/librocblas.so /opt/amdgpu/lib/x86_64-linux-gnu/librocsparse.so /opt/amdgpu/lib/x86_64-linux-gnu/librocfft.so /opt/amdgpu/lib/x86_64-linux-gnu/libamdhip64.so /opt/amdgpu/lib/x86_64-linux-gnu/libOpenCL.so /opt/amdgpu/lib/x86_64-linux-gnu/libhiprand.so /opt/amdgpu/lib/x86_64-linux-gnu/libhipfft.so /opt/amdgpu/lib/x86_64-linux-gnu/libhsa-runtime64.so /opt/amdgpu/lib/x86_64-linux-gnu/libhsakmt.a /opt/amdgpu/lib/x86_64-linux-gnu/libamd_comgr.so"

# export PROFILE_TASK="-m test --pgo-extended -j25 --timeout=1200"
# export BOLT_APPLY_FLAGS="-update-debug-sections --use-gnu-stack  -reorder-blocks=ext-tsp --frame-opt-rm-stores --use-aggr-reg-reassign --use-compact-aligner  --use-edge-counts  --x86-align-branch-boundary-hot-only  --x86-strip-redundant-address-size --frame-opt=all --cg-from-perf-data -reorder-functions=hfsort+ --eliminate-unreachable -split-functions --align-blocks -icf=1 --sequential-disassembly -split-eh -reorder-functions-use-hot-size -peepholes=none -jump-tables=aggressive -inline-ap -indirect-call-promotion=all -dyno-stats -use-gnu-stack -frame-opt=hot"
# make regen-all
# make regen-stdlib-module-names
# make regen-limited-abi
# make regen-configure
# autoreconf -ivf -Werror
# ./configure --prefix="/home/remi/.pyenv/versions/3.12-rocm6v4" --enable-optimizations --with-lto=thin --enable-bolt 
# make all -j25 
# make altinstall


# export PATH="/opt/rocm/llvm/alt/bin/llvm-*:$PATH:"
# export LDFLAGS="-flto" 
# export LIBS="-lblis -lfftw3 -lamdlibm -lscalapack -lrocblas -lrocsparse -lrocfft -lamdhip64 -lOpenCL -lhiprand -lhipfft -lhsa-runtime64 -lhsakmt -lamd_comgr"
  