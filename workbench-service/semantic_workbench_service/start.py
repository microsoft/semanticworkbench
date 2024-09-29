import argparse
import logging

import uvicorn
from fastapi import FastAPI

from . import logging_config, service, settings
from .api import FastAPILifespan

logging_config.config(settings=settings.logging)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    lifespan = FastAPILifespan()
    app = FastAPI(lifespan=lifespan.lifespan, title="Semantic Workbench Service", version="0.1.0")
    service.init(
        app,
        register_lifespan_handler=lifespan.register_handler,
    )
    return app


def main():
    parse_args = argparse.ArgumentParser(
        description="start the Semantic workbench service", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parse_args.add_argument(
        "--host",
        dest="host",
        type=str,
        default=settings.service.hostname,
        help="host IP to run service on",
    )
    parse_args.add_argument(
        "--port", dest="port", type=int, default=settings.service.port, help="port to run service on"
    )
    args = parse_args.parse_args()

    settings.service.hostname = args.host
    settings.service.port = args.port

    logger.info("Starting workbench service ...")
    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, log_config={"version": 1, "disable_existing_loggers": False})


if __name__ == "__main__":
    main()
