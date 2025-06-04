"""
Filtros y búsquedas para incidentes
"""

import re
from datetime import datetime, timedelta
from typing import Iterator, Optional, Callable
from collections.abc import Iterable
from .models import Incident


class IncidentFilter:
    """Clase para filtrar incidentes con diferentes criterios"""

    @staticmethod
    def by_text(incidents: Iterable[Incident], pattern: str) -> Iterator[Incident]:
        """Filtrar por texto usando regex en descripción"""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            for incident in incidents:
                if regex.search(incident.description):
                    yield incident
        except re.error:
            # Si el regex es inválido, buscar texto literal
            pattern_lower = pattern.lower()
            for incident in incidents:
                if pattern_lower in incident.description.lower():
                    yield incident

    @staticmethod
    def by_type(incidents: Iterable[Incident], incident_type: str) -> Iterator[Incident]:
        """Filtrar por tipo de incidente"""
        for incident in incidents:
            if incident.type == incident_type:
                yield incident

    @staticmethod
    def by_operator(incidents: Iterable[Incident], operator: str) -> Iterator[Incident]:
        """Filtrar por operador asignado"""
        for incident in incidents:
            if incident.assigned_to == operator:
                yield incident

    @staticmethod
    def by_status(incidents: Iterable[Incident], status: str) -> Iterator[Incident]:
        """Filtrar por estado"""
        for incident in incidents:
            if incident.status == status:
                yield incident

    @staticmethod
    def by_priority(incidents: Iterable[Incident], priority: str) -> Iterator[Incident]:
        """Filtrar por prioridad"""
        for incident in incidents:
            if incident.priority == priority:
                yield incident

    @staticmethod
    def by_date_range(incidents: Iterable[Incident],
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> Iterator[Incident]:
        """Filtrar por rango de fechas"""
        for incident in incidents:
            if start_date and incident.created_at < start_date:
                continue
            if end_date and incident.created_at > end_date:
                continue
            yield incident

    @staticmethod
    def expired_incidents(incidents: Iterable[Incident], minutes: int = 30) -> Iterator[Incident]:
        """Filtrar incidentes que han superado el tiempo límite"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        for incident in incidents:
            if (incident.status in ["pending", "in_progress"] and
                    incident.created_at < cutoff_time):
                yield incident


def create_composite_filter(*filters: Callable[[Iterable[Incident]], Iterator[Incident]]) -> Callable[
    [Iterable[Incident]], Iterator[Incident]]:
    """Crear un filtro compuesto que aplica múltiples filtros en secuencia"""

    def composite_filter(incidents: Iterable[Incident]) -> Iterator[Incident]:
        result = incidents
        for filter_func in filters:
            result = filter_func(result)
        return result

    return composite_filter