from config import LoggerSetup, log_execution
import functools

# Configurar logger
logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)


@log_execution("procesar_datos_jugador")
@functools.lru_cache(maxsize=100)
def main():
    """
    

    Args:

    Returns:

    """

    logger.info("")
    logger.debug("")

    if 1 != 0:
        raise ValueError("")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Error en ejecución principal: {e}")