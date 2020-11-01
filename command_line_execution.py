from argparse import ArgumentParser
import asyncio
import logging
import time

from reporter.bridge import Bridge

logging.basicConfig(
    filename='reporter.log',
    level=logging.INFO,
    format='%(asctime)-15s %(levelname)-8s %(message)s',
)


async def main(sprint_number):
    """Execute the script in a event loop."""
    await Bridge(sprint_number).run()


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Spam bot to send notifications about pull requests to slack.',
    )
    parser.add_argument('--sprint', help='Sprint number')
    args = parser.parse_args()

    start = time.time()
    asyncio.run(main(args.sprint))
    print(f'time: {time.time() - start}')
