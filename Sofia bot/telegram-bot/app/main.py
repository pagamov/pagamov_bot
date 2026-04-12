import asyncio
import logging
import structlog
from app.bot import SofiaBot


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ]
    )


def main():
    setup_logging()
    logger = structlog.get_logger()
    logger.info("starting_sofia_bot")
    
    bot = SofiaBot()
    bot.run()


if __name__ == "__main__":
    main()
