import asyncio
import time
from multiprocessing.pool import Pool as ProcessPool
from multiprocessing.pool import ThreadPool
import inspect 
from threading import Thread
from remiloop import remasync, remawait
import requests
import pandas as pd

import aiohttp
# CLIENT = aiohttp.ClientSession()


def fib(*args):
    n = args[0]
    if not isinstance(n, int):
        print('got n = ', n, 'type = ', type(n), 'args = ', args, 'len = ', len(args))
    return n if n < 2 else fib(n - 2) + fib(n - 1)

async def VAR_hist_9D(symbol, session):
    async with session.get(f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}USDT&interval=1d&limit=1500') as r:
        df = pd.DataFrame(await r.json())
    df = df[[0, 4]]
    df.columns = ['time', 'close']
    df['time'] = df['time'].apply(lambda x: pd.Timestamp(x*1e6))
    df['close'] = df['close'].astype(float)
    res = {}
    for p in [0, 0.01, 0.025, 0.05, 0.1]:
        res[p] = (df['close'].rolling(9).max() / df['close'].shift(9) -1).quantile(1 - p)
    return res

# async def t(k):   
#     #example
#     return fib(k)

# @remasync
# async def t_r(k):
#     #example
#     return await t(k)

def ensure_async(func):
    """
    Ensure that a function is async. If it's not, wrap it in an async function.
    """
    if asyncio.iscoroutinefunction(func) or inspect.iscoroutinefunction(func):
        # The function is already a coroutine
        return func
    else:
        async def wrapped(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapped


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def sequentials(func, arglist):
    return tuple(func(arg) for args in arglist for arg in args)

async def main_asyncio(func, arglist):
    func = ensure_async(func)
    coros = tuple(func(*args) for args in arglist)
    res = tuple(await asyncio.gather(*coros))
    return res

def main_reamsync(func, arglist):
    func = remasync(ensure_async(func))
    remawaitables = tuple(func(*args) for args in arglist)
    return tuple(remawait(*remawaitables))

def main_proces_map_async(func, arglist):
    with ProcessPool() as pool:
        return tuple(pool.map_async(func=func, iterable=(arg for args in arglist for arg in args)).get())

def main_process(func, arglist):
    with ProcessPool() as pool:
        return tuple(pool.map(func = func, iterable = (arg for args in arglist for arg in args)))


def main_threaded(func, arglist):
    threads = []
    for args in arglist:
        threads.append(ThreadWithReturnValue(target=func, args=args))
        threads[-1].start()
    return tuple(t.join() for t in threads)
    

def main_thread_pool(func, arglist):
    with ThreadPool() as pool:
        return tuple(pool.map(func = func, iterable = (arg for args in arglist for arg in args)))

def main_thread_pool_map_async(func, arglist):
    with ThreadPool() as pool:
        return tuple(pool.map_async(func=func, iterable=(arg for args in arglist for arg in args)).get())
  

async def compare_methods(comparison_func, comparison_arglist, verbose = False):
    print(f'Start comparing execution methods for {comparison_func.__name__} over {comparison_arglist}')
    results_dict = {}

    # # Sequential
    # t1 = time.time()
    # results_dict['Sequentials'] = (sequentials(comparison_func, comparison_arglist), time.time() - t1)
    # verbose and print('Sequentials finished')

    # Async standard
    t1 = time.time()
    results_dict['Async standard'] = (await (main_asyncio(comparison_func, comparison_arglist)), time.time() - t1)
    verbose and print('Async standard finished')

    # Reamsync
    t1 = time.time()
    results_dict['Reamsync'] = (main_reamsync(comparison_func, comparison_arglist), time.time() - t1)
    verbose and print('Reamsync finished')

    # # Thread with ThreadWithReturnValue class
    # t1 = time.time()
    # results_dict['Thread with ThreadWithReturnValue class'] = (main_threaded(comparison_func, comparison_arglist), time.time() - t1)
    # verbose and print('Thread with ThreadWithReturnValue class finished')

    # # Thread Pool pool
    # t1 = time.time()
    # results_dict['Thread Pool pool'] = (main_thread_pool(comparison_func, comparison_arglist), time.time() - t1)
    # verbose and print('Thread Pool pool finished')

    # # Thread Pool pool map async
    # t1 = time.time()
    # results_dict['Thread Pool pool map async'] = (main_thread_pool_map_async(comparison_func, comparison_arglist), time.time() - t1)
    # verbose and print('Thread Pool pool map async finished')

    # # Process Pool
    # t1 = time.time()
    # results_dict['Process Pool'] = (main_process(comparison_func, comparison_arglist), time.time() - t1)
    # verbose and print('Process Pool finished')

    # # Process Pool map async
    # t1 = time.time()
    # results_dict['Process Pool map async'] = (main_proces_map_async(comparison_func, comparison_arglist), time.time() - t1)
    # verbose and print('Process Pool map async finished')


    # base_results = results_dict['Sequentials'][0]
    # print(f"Base results in sequential execution:\n{base_results}")
    # # Print the results
    for name, (result, exec_time) in results_dict.items():
        print(f"{name}: {exec_time} seconds")
    #     if result != base_results:
    #         print(f"WARNING: {name} result are different from the base result\n{result}")


comparison_func = fib
comparison_arglist = [(30,), (31,), (35,)]
# comparison_arglist = [(30,), (31,), (35,) , (39,)]
# compare_methods(comparison_func, comparison_arglist, verbose = True)
async def main():
    async with aiohttp.ClientSession() as session:
        comparison_func = VAR_hist_9D
        comparison_arglist = [('ATOM',), ('AVAX',), ('ALGO',), ('BTC',), ('ETH',), ('XRP',)]
        comparison_arglist = [('ATOM',session), ('AVAX',session), ('ALGO',session), ('BTC',session), ('ETH',session), ('XRP',session)]
        await compare_methods(comparison_func, comparison_arglist, verbose = True)
asyncio.run(main())

# t1 = time.time()
# sequentials_results = sequentials(comparison_func, comparison_arglist)
# print('Sequentials', time.time()-t1)

# t1=time.time()
# async_results = asyncio.run(main_asyncio(comparison_func, comparison_arglist))
# print('Async standard', time.time()-t1)

# t1=time.time()
# remasync_results = main_reamsync(comparison_func, comparison_arglist)
# print('Reamsync', time.time()-t1)

# t1=time.time()
# threaded_results = main_threaded(comparison_func, comparison_arglist)
# print('Thread with ThreadWithReturnValue class', time.time()-t1)

# t1=time.time()
# threadpool_result = main_thread_pool(comparison_func, comparison_arglist)
# print('Thread Pool pool', time.time()-t1)

# t1=time.time()
# thread_pool_map_async_result = main_thread_pool_map_async(comparison_func, comparison_arglist)
# print('Thread Pool pool map async', time.time()-t1)

# t1=time.time()
# process_pool_results = main_process(comparison_func, comparison_arglist)
# print('Process Pool', time.time()-t1)

# t1=time.time()
# process_pool_map_async_result = main_proces_map_async(comparison_func, comparison_arglist)
# print('Process Pool map async', time.time()-t1)

# import pandas as pd
# import requests

# fd = {}
# for symbol in ['ATOM', 'AVAX', 'ALGO']:
#   r = requests.get(f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}USDT&interval=1d&limit=1500')
#   df = pd.DataFrame(r.json())
#   df = df[[0, 4]]
#   df.columns = ['time', 'close']
#   df['time'] = df['time'].apply(lambda x: pd.Timestamp(x*1e6))
#   df['close'] = df['close'].astype(float)
#   fd[symbol] = {}
#   for p in [0, 0.01, 0.025, 0.05, 0.1]:
#     fd[symbol][p] = (df['close'].rolling(9).max() / df['close'].shift(9) -1).quantile(1 - p)

# print(fd)
