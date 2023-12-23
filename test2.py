from remiloop import remasync
import asyncio
import time
import random

@remasync#()
async def async_function(value, pow, sleep_time=random.random()):
    await asyncio.sleep(sleep_time)
    return value ** pow

@remasync#()
async def async_function_two(value, other_value, sleep_time=random.random()):
    await asyncio.sleep(sleep_time)
    return value - other_value

@remasync#()
def listsyncfunc(l1, l2):
    if len(l1) != len(l2):
        raise ValueError('Lists must be of equal length')
    return [item_1 // item_2 for item_1, item_2 in zip(l1, l2)]

@remasync#()
def sync_function(value, pow, sleep_time=random.random()):
    time.sleep(sleep_time)
    return value ** pow


def normal_func(value, pow_div, nmax):
    return [async_function(value, i/pow_div, random.random()) for i in range(nmax)]



def launch_comp():

    base_timers = {}
    count = 0
    
    t1 = time.time()
    a = async_function(2, 1)
    if a:
        print('bool a is True',a)
        b = async_function(4.4, 1)
    else:
        b = async_function(4.4, 2)

    a += b
    print('a,b', a, b)
    base_timers[count] = time.time() - t1
    count += 1
    t1 = time.time()
    
    
    a = async_function(0, 1)
    if a:
        print('bool a is True',a)
        b = async_function(4.4, 1)
    else:
        b = async_function(4.4, 2)
    b += a
    print('a,b', a, b)

    print(f'{a} {b} {a+b}')

    base_timers[count] = time.time() - t1
    count += 1
    t1 = time.time()

    t1 = time.time()
    a, b = async_function(2, 1, 2), async_function(4.4, 1, 1)
    a += b
    print(b)
    base_timers[count] = time.time() - t1
    count += 1
    t1 = time.time()

    t1 = time.time()
    a, b = async_function(2, 1, 2), async_function(4.4, 1, 1)
    a += b
    print(a)
    base_timers[count] = time.time() - t1
    count += 1
    t1 = time.time()

    t1 = time.time()
    a, b = async_function(2, 1, 1), async_function(4.4, 1, 2)
    a += b
    print(b)
    base_timers[count] = time.time() - t1
    count += 1
    t1 = time.time()

    t1 = time.time()
    a, b = async_function(2, 1, 1), async_function(4.4, 1, 2)
    a += b
    print(a)
    print('a2 time', time.time() - t1)

    t1 = time.time()
    a, b = async_function(2.4, 1, 1), async_function(4, 1, 2)
    b += a
    print(b)
    print('b3 time', time.time() - t1)

    t1 = time.time()
    a, b = async_function(2.4, 1, 1), async_function(4, 1, 2)
    print(time.time() - t1)
    b += a
    print(time.time() - t1)
    print(a)
    print(time.time() - t1)
    print('a3 time', time.time() - t1)

    t1 = time.time()
    l = [async_function(3, i, (5 - i)/2) for i in range(5)]
    print(l)
    print('time', time.time() - t1)

    t1 = time.time()
    l = [async_function(3, i, (5 - i)/2) for i in range(5)]
    l[-1] *= 4
    print(l[-1], l[-2])
    
    t1 = time.time()
    a, b = async_function(3, 2, 1), async_function(4, 2, 1)
    c = async_function_two(b, 17.34, 1.5)
    print(a + c)
    print('time', time.time() - t1)

    timers = {'a': 0, 'b': 0, 'c': 0}

    for _ in range(5):

        t1 = time.time()
        l = normal_func(2.5, 10, 3)
        l2 = normal_func(2.5, 10, 3)
        print(l)
        print(l2)
        l3 = listsyncfunc(l, l2)
        print(l3)
        timers['a'] += time.time() - t1
        
        del l, l2, l3

        t1 = time.time()
        l = normal_func(2.5, 10, 3)
        l2 = normal_func(2.5, 10, 3)
        l3 = listsyncfunc(l, l2)
        print(l)
        print(l2)
        print(l3)
        timers['b'] += time.time() - t1
        del l, l2, l3

        t1 = time.time()
        l = normal_func(2.5, 10, 3)
        l2 = normal_func(2.5, 10, 3)
        l3 = listsyncfunc(l, l2)
        print(l3)
        print(l2)
        print(l)
        timers['c'] += time.time() - t1
        del l, l2, l3
    print('Timers:', timers)

# Asynchronous context
async def run_async(func, *args):
    return func(*args)
    # print(f"Async result: {result}")

# Synchronous context
def run_sync(func, *args):
    return func(*args)
    
@remasync#(1)
def fib(n):
    return n if n < 2 else fib(n - 2) + fib(n - 1)


def launch_recursive():
    t1 = time.time()
    fib_1 = fib(3)
    print(type(fib_1))
    print('fib1 result:', fib_1)
    print(time.time() - t1)

    # t1 = time.time()
    # fib_1 = fib(20)
    # print(type(fib_1))
    # print('fib1 result:', fib_1)
    # print(time.time() - t1)

if __name__ == '__main__':
    launch_recursive()

    # t1 = time.time()
    # asyncio.run(run_async(launch_comp))
    # inside_a_main_async_loop = time.time() - t1
    # t1 = time.time()
    # run_sync(launch_comp)
    # without_a_main_async_loop = time.time() - t1

    # print('inside_a_main_async_loop', inside_a_main_async_loop)
    # print('without_a_main_async_loop', without_a_main_async_loop)
