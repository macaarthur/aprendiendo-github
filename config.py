import logging
import os

from dotenv import load_dotenv


load_dotenv()


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging():
	logging.basicConfig(
		level=getattr(logging, LOG_LEVEL, logging.DEBUG),
		format=LOG_FORMAT,
	)
