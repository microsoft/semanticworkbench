import argparse
import logging
import os
import socket
import sys
from contextlib import closing

import uvicorn

from . import logging_config, settings

logger = logging.getLogger(__name__)
logging.getLogger(sys.modules[__name__].__package__).setLevel(logging.DEBUG)


def main():
    logging_config.config(settings=settings.logging)

    parse_args = argparse.ArgumentParser(
        description="start a FastAPI assistant service", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parse_args.add_argument(
        "--app",
        type=str,
        help="assistant app to start; ex: workbench_assistant.canonical:app",
        default=os.getenv("ASSISTANT_APP", "assistant:app"),
    )
    parse_args.add_argument(
        "--port",
        dest="port",
        type=int,
        help="port to run service on; if not specified or 0, a random port will be selected",
        default=settings.port,
    )
    parse_args.add_argument("--host", dest="host", type=str, default=settings.host, help="host IP to run service on")
    parse_args.add_argument(
        "--assistant-service-id",
        dest="assistant_service_id",
        type=str,
        help="Override the assistant service ID",
        default=settings.assistant_service_id,
    )
    parse_args.add_argument(
        "--assistant-service-name",
        dest="assistant_service_name",
        type=str,
        help="Override the assistant service name",
        default=settings.assistant_service_name,
    )
    parse_args.add_argument(
        "--assistant-service-description",
        dest="assistant_service_description",
        type=str,
        help="Override the assistant service description",
        default=settings.assistant_service_description,
    )
    parse_args.add_argument(
        "--assistant-service-url",
        dest="assistant_service_url",
        type=str,
        help="Override the assistant service URL",
        default=settings.assistant_service_url,
    )
    parse_args.add_argument(
        "--workbench-service-url",
        dest="workbench_service_url",
        type=str,
        help="Override the workbench service URL",
        default=settings.workbench_service_url,
    )
    parse_args.add_argument(
        "--reload", dest="reload", nargs="?", action="store", type=str, default="false", help="enable auto-reload"
    )

    args = parse_args.parse_args()

    assistant_root_module = args.app.split(":")[0].split(".")[0]
    logging.getLogger(assistant_root_module).setLevel(logging.DEBUG)

    logger.info(f"Starting '{args.app}' assistant service ...")
    reload = args.reload != "false"
    if reload:
        logger.info("Enabling auto-reload ...")

    settings.host = args.host
    settings.port = args.port or find_free_port(settings.host)
    settings.assistant_service_id = args.assistant_service_id
    settings.assistant_service_name = args.assistant_service_name
    settings.assistant_service_description = args.assistant_service_description
    settings.assistant_service_url = args.assistant_service_url
    settings.workbench_service_url = args.workbench_service_url

    uvicorn.run(
        args.app,
        host=settings.host,
        port=settings.port,
        reload=reload,
        log_config={"version": 1, "disable_existing_loggers": False},
    )


def find_free_port(host: str):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind((host, 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


if __name__ == "__main__":
    main()
