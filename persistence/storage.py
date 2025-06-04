"""
Gestión de persistencia de datos
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class StorageManager:
    """Gestor de almacenamiento de datos"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.incidents_file = self.data_dir / "incidents.json"
        self.backup_dir = self.data_dir / "backups"
        self._ensure_directories()

    def _ensure_directories(self):
        """Crear directorios necesarios"""
        try:
            self.data_dir.mkdir(exist_ok=True)
            self.backup_dir.mkdir(exist_ok=True)
            logger.info(f"Directorios de almacenamiento verificados: {self.data_dir}")
        except Exception as e:
            logger.error(f"Error creando directorios: {e}")
            raise

    def save_incidents(self, incidents_data: List[Dict[str, Any]]):
        """Guardar incidentes en JSON"""
        try:
            # Crear backup si existe archivo previo
            if self.incidents_file.exists():
                self._create_backup()

            # Guardar datos
            with open(self.incidents_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'incidents': incidents_data
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"Guardados {len(incidents_data)} incidentes")

        except Exception as e:
            logger.error(f"Error guardando incidentes: {e}")
            raise

    def load_incidents(self) -> List[Dict[str, Any]]:
        """Cargar incidentes desde JSON"""
        try:
            if not self.incidents_file.exists():
                logger.info("No se encontró archivo de incidentes, iniciando con datos vacíos")
                return []

            with open(self.incidents_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            incidents = data.get('incidents', [])
            logger.info(f"Cargados {len(incidents)} incidentes desde archivo")
            return incidents

        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error cargando incidentes: {e}")
            return []

    def _create_backup(self):
        """Crear backup del archivo actual"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"incidents_backup_{timestamp}.json"

            import shutil
            shutil.copy2(self.incidents_file, backup_file)

            # Mantener solo los últimos 5 backups
            self._cleanup_old_backups()

            logger.info(f"Backup creado: {backup_file}")

        except Exception as e:
            logger.warning(f"Error creando backup: {e}")

    def _cleanup_old_backups(self, keep_count: int = 5):
        """Limpiar backups antiguos"""
        try:
            backup_files = sorted(
                [f for f in self.backup_dir.glob("incidents_backup_*.json")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                logger.info(f"Backup antiguo eliminado: {old_backup}")

        except Exception as e:
            logger.warning(f"Error limpiando backups: {e}")