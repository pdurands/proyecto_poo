
"""
Simulador de Gestión de Incidentes y Flujos de Escalamiento
Punto de entrada principal del sistema
"""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al path para imports
sys.path.append(str(Path(__file__).parent))

from cli.interface import IncidentManagerCLI
from core.dispatcher import IncidentDispatcher
from persistence.storage import StorageManager
import logging


def setup_logging():
    """Configurar sistema de logging"""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/events.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """Función principal del sistema"""
    try:
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Iniciando Simulador de Gestión de Incidentes")

        # Inicializar componentes
        storage = StorageManager()
        dispatcher = IncidentDispatcher(storage)
        cli = IncidentManagerCLI(dispatcher)

        # Ejecutar interfaz CLI
        cli.run()

    except KeyboardInterrupt:
        print("\n👋 Sistema cerrado por el usuario")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        logging.error(f"Error crítico en main: {e}", exc_info=True)
    finally:
        logging.info("Sistema cerrado")


if __name__ == "__main__":
    main()