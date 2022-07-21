import asyncio
import logging
import sys

from configobj import ConfigObj

from coned_rtu import Config, Pyppeteer

logging.basicConfig(level=logging.INFO)

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <config file>")
    sys.exit(1)

cfg_obj = ConfigObj(sys.argv[1])
config = Config.from_config_obj(cfg_obj)
coned = Pyppeteer(config)


async def main():
    await coned.__ainit__()
    await coned.login()
    usage_json = await coned.get_usage()
    print(usage_json)


asyncio.run(main())
