"""
Sistema de escalamiento de incidentes
"""

from datetime import datetime, timedelta
from typing import Protocol, Callable, Iterator
from collections.abc import Iterable
from incident.models import Incident
import logging

logger = logging.getLogger(__name__)


class EscalationStrategy(Protocol):
    """Protocolo para estrategias de escalamiento"""

    def should_escalate(self, incident: Incident) -> bool:
        """Determinar si un incidente debe escalarse"""
        ...


class TimeBasedEscalation:
    """Escalamiento basado en tiempo"""

    def __init__(self, minutes_threshold: int = 30):
        self.minutes_threshold = minutes_threshold

    def should_escalate(self, incident: Incident) -> bool:
        """Escalar si ha pasado más tiempo del umbral"""
        if incident.status not in ["pending", "in_progress"]:
            return False

        time_elapsed = datetime.now() - incident.created_at
        return time_elapsed > timedelta(minutes=self.minutes_threshold)


class PriorityBasedEscalation:
    """Escalamiento basado en prioridad"""

    def __init__(self, auto_escalate_high: bool = True):
        self.auto_escalate_high = auto_escalate_high

    def should_escalate(self, incident: Incident) -> bool:
        """Escalar automáticamente incidentes de alta prioridad antiguos"""
        if not self.auto_escalate_high or incident.priority != "high":
            return False

        if incident.status not in ["pending", "in_progress"]:
            return False

        # Escalar incidentes de alta prioridad después de 15 minutos
        time_elapsed = datetime.now() - incident.created_at
        return time_elapsed > timedelta(minutes=15)


class CompositeEscalation:
    """Escalamiento compuesto que combina múltiples estrategias"""

    def __init__(self, *strategies: EscalationStrategy):
        self.strategies = strategies

    def should_escalate(self, incident: Incident) -> bool:
        """Escalar si cualquier estrategia lo indica"""
        return any(strategy.should_escalate(incident) for strategy in self.strategies)


def create_escalation_closure(strategy: EscalationStrategy) -> Callable[[Incident], bool]:
    """Crear un closure para estrategia de escalamiento"""

    def escalation_func(incident: Incident) -> bool:
        try:
            return strategy.should_escalate(incident)
        except Exception as e:
            logger.error(f"Error en estrategia de escalamiento: {e}")
            return False

    return escalation_func


class IncidentEscalator:
    """Gestor de escalamiento de incidentes"""

    def __init__(self, strategy: EscalationStrategy = None):
        self.strategy = strategy or CompositeEscalation(
            TimeBasedEscalation(30),
            PriorityBasedEscalation(True)
        )

    def find_escalatable_incidents(self, incidents: Iterable[Incident]) -> Iterator[Incident]:
        """Encontrar incidentes que deben escalarse"""
        for incident in incidents:
            if self.strategy.should_escalate(incident):
                logger.info(f"Incidente {incident.id} marcado para escalamiento")
                yield incident

    def escalate_incident(self, incident: Incident) -> Incident:
        """Escalar un incidente específico"""
        logger.warning(f"Escalando incidente {incident.id}: {incident.description[:50]}...")
        return incident.with_status("escalated")
