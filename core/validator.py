"""
Validadores para el sistema de incidentes
"""

import re
from datetime import datetime
from typing import Optional, Callable, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def validate_input(validator_func: Callable[[Any], bool], error_message: str):
    """Decorador para validar entrada de funciones"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validar el primer argumento después de self
            if len(args) > 1 and not validator_func(args[1]):
                logger.warning(f"Validación fallida: {error_message}")
                raise ValueError(error_message)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_operation(operation_name: str):
    """Decorador para registrar operaciones"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"Iniciando operación: {operation_name}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Operación completada: {operation_name}")
                return result
            except Exception as e:
                logger.error(f"Error en operación {operation_name}: {e}")
                raise

        return wrapper

    return decorator


class IncidentValidator:
    """Validador para datos de incidentes"""

    VALID_TYPES = {"infrastructure", "security", "application"}
    VALID_PRIORITIES = {"high", "medium", "low"}
    VALID_STATUSES = {"pending", "in_progress", "resolved", "escalated"}

    @classmethod
    def validate_type(cls, incident_type: str) -> bool:
        """Validar tipo de incidente"""
        return incident_type in cls.VALID_TYPES

    @classmethod
    def validate_priority(cls, priority: str) -> bool:
        """Validar prioridad"""
        return priority in cls.VALID_PRIORITIES

    @classmethod
    def validate_status(cls, status: str) -> bool:
        """Validar estado"""
        return status in cls.VALID_STATUSES

    @classmethod
    def validate_description(cls, description: str) -> bool:
        """Validar descripción (no vacía y longitud razonable)"""
        return isinstance(description, str) and 5 <= len(description.strip()) <= 500

    @classmethod
    def validate_operator_name(cls, name: str) -> bool:
        """Validar nombre de operador"""
        if not isinstance(name, str):
            return False
        # Solo letras, números y espacios, 2-50 caracteres
        return bool(re.match(r'^[a-zA-Z0-9\s]{2,50}$', name.strip()))

    @classmethod
    def validate_all_incident_data(cls, incident_type: str, priority: str, description: str) -> list[str]:
        """Validar todos los datos de un incidente, retornar lista de errores"""
        errors = []

        if not cls.validate_type(incident_type):
            errors.append(f"Tipo inválido. Debe ser uno de: {', '.join(cls.VALID_TYPES)}")

        if not cls.validate_priority(priority):
            errors.append(f"Prioridad inválida. Debe ser una de: {', '.join(cls.VALID_PRIORITIES)}")

        if not cls.validate_description(description):
            errors.append("Descripción debe tener entre 5 y 500 caracteres")

        return errors