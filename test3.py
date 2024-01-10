# import asyncio

# async def fib(n):
#     print("in fib with n=",n)
#     res = n if n < 2 else await fib(n - 2) + await fib(n - 1)
#     print("in fib with n=",n,"res=",res)
#     return res

# async def main():
#     fib_1 = await fib(4)
#     print(type(fib_1))
#     print('fib1 result:', fib_1)

#     fib_2 = await fib(20)
#     print(type(fib_2))
#     print('fib2 result:', fib_2)

# if __name__ == '__main__':
#     asyncio.run(main())


import asyncio
import functools

def remasync(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper

@remasync
async def fib(n):
    print("in fib with n=", n)
    if n < 2:
        return n
    return await fib(n - 1) + 5  # Correctly await the recursive call

async def launch_recursive():
    fib_1 = await fib(3)
    print('fib result:', fib_1)

# Run the async function
asyncio.run(launch_recursive())