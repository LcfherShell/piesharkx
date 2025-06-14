import logging, os

__all__ = ["logger"]
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("pieshark.log")],
)
logger = logging.getLogger("pieshark")