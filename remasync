import asyncio
from threading import Thread
import inspect
from concurrent.futures import TimeoutError, ProcessPoolExecutor

def ensure_async(func):
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
        # print('INIT', func, args, kwargs)
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._future = None
        self.__awaited = False
        self._loop = secondary_loop.get_loop()
        if not contains_awaitable(args, remawaitable) and not contains_awaitable(kwargs, remawaitable):
            # print(func, args, kwargs)
            self._future = asyncio.run_coroutine_threadsafe(self._func(*self._args, **self._kwargs), self._loop)
        
    @property
    def result(self):
        if not self.__awaited:
            self.__await__()
        return self.__result

    def __await__(self):
        if self._future is None:
            self._args, self._kwargs = any_apply((self._args, self._kwargs), lambda_select = lambda x: isinstance(x, remawaitable), lambda_apply = lambda x: x.result)
            self._future = asyncio.run_coroutine_threadsafe(self._func(*self._args, **self._kwargs), self._loop)
        print('all tasks: ',asyncio.all_tasks(self._loop._loop))
        try:
            self.__result = self._future.result(7)
        except TimeoutError as te:
            print('TimeoutError moving to ProcessPoolExecutor')
            self._future = self._loop.run_in_executor(self._loop._executor, self._func, *self._args, **self._kwargs)
        # self.__result = self._future.result()
        self.__awaited = True
        return self

    @classmethod
    def make_dunder(cls, method):
        def dunder(self, *args, **kwargs):
            args, kwargs = any_apply((args, kwargs), lambda_select = lambda x: isinstance(x, remawaitable), lambda_apply = lambda x: x.result)
            if isinstance(self, cls):
                self = self.result
            if not isinstance((res := getattr(self.__class__, method)(self, *args, **kwargs)), NotImplemented.__class__):
                return res
            elif method in RMETHODS and (other:=args[0] if args else kwargs.get('other', None)) and (rm := getattr(other, RMETHODS.get(method))):
                return rm(self, *args[1:], **{k: v for k, v in kwargs.items() if k != 'other'})
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


# func.depth += 1

def remasync(func):
    def wrapper(*args, **kwargs):
        return remawaitable(ensure_async(func), *args, **kwargs)
    return wrapper


# import functools

# def remasync(n=1):
#     def decorator(func):
#         afunc = ensure_async(func)

#         if not hasattr(func, "depth"):
#             print('NO HAS')
#             func.depth = 0

#         @functools.wraps(afunc)
#         def wrapper(*d_args, **d_kwargs):
#             # Increment the depth counter
#             try:
#                 # Apply behavior only in the first n calls (external layers)
#                 if func.depth <= n:
#                     func.depth += 1
#                     return remawaitable(afunc, *d_args, **d_kwargs)
#                 else:
#                     r = func(*d_args, **d_kwargs)
#                     return r
#             finally:
#                 # Decrement the depth counter
#                 func.depth -= 1
                

#         return wrapper
#     return decorator



# def remasync(n=1):
#     def decorator(func):
#         # Use a function attribute to track recursion depth
#         if not hasattr(func, "depth"):
#             func.depth = 0
        
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):

#             # Increment the depth counter
#             # func.depth += 1
#             # try:
                
#             #     if func.depth <= n:
#             args = (ensure_async(func), *args)
#             func = remawaitable
#             return func(*args, **kwargs)
#             # finally:
#             #     func.depth -= 1

#         return wrapper
#     return decorator

