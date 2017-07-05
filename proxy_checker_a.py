import asyncio
import csv

import aiohttp

WEBSITE = 'https://www.google.com'
OUT_FILE_NAME = 'proxy_timeouts.txt'

with open(OUT_FILE_NAME, 'w') as exit_file:

    async def fetch(proxy):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(WEBSITE,
                                       proxy=proxy):
                    return proxy

        except aiohttp.ClientConnectorError as e:
            print('proxy', proxy, 'with ClientConnectorError: ', e)
            if e.errno == 110:
                exit_file.write(proxy + '\n')
        except aiohttp.ServerDisconnectedError as e:
            print('proxy', proxy, 'with ServerDisconnectedError: ', e)
        except TimeoutError:
            exit_file.write(proxy)
        except Exception as e:
            # exit_file.write(proxy)
            print('bad proxy', proxy, e)

    async def bound_fetch(proxy, sem):
        # Getter function with semaphore.
        async with sem:
            await fetch(proxy)

    async def main():
        tasks = []
        with open('proxylist.csv') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            sem = asyncio.Semaphore(1000)  # reduce concurrent request number
            for row in spamreader:
                if 'ip' in row:
                    continue
                # csv proxy format: user password ip port
                proxy = 'http://' + row[2] + ':' + row[-1] + '@'+ row[0] + ':' + row[1]

                task = asyncio.ensure_future(bound_fetch(proxy, sem))
                tasks.append(task)

            for r in asyncio.as_completed(tasks):
                await r

    parsed_data = asyncio.get_event_loop().run_until_complete(main())
