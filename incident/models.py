"""
Modelos de datos para el sistema de gestión de incidentes
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal
import json

IncidentType = Literal["infrastructure", "security", "application"]
Priority = Literal["high", "medium", "low"]
Status = Literal["pending", "in_progress", "resolved", "escalated"]


@dataclass(frozen=True, slots=True)
class Incident:
    """Estructura de un incidente"""
    id: int
    type: IncidentType
    priority: Priority
    description: str
    created_at: datetime
    assigned_to: Optional[str]
    status: Status

    def to_dict(self) -> dict:
        """Convertir a diccionario para serialización JSON"""
        return {
            'id': self.id,
            'type': self.type,
            'priority': self.priority,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'assigned_to': self.assigned_to,
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Incident':
        """Crear instancia desde diccionario"""
        return cls(
            id=data['id'],
            type=data['type'],
            priority=data['priority'],
            description=data['description'],
            created_at=datetime.fromisoformat(data['created_at']),
            assigned_to=data['assigned_to'],
            status=data['status']
        )

    def with_status(self, new_status: Status) -> 'Incident':
        """Crear nueva instancia con estado actualizado"""
        return Incident(
            id=self.id,
            type=self.type,
            priority=self.priority,
            description=self.description,
            created_at=self.created_at,
            assigned_to=self.assigned_to,
            status=new_status
        )

    def with_assignment(self, operator: str) -> 'Incident':
        """Crear nueva instancia con operador asignado"""
        return Incident(
            id=self.id,
            type=self.type,
            priority=self.priority,
            description=self.description,
            created_at=self.created_at,
            assigned_to=operator,
            status="in_progress"
        )


@dataclass(frozen=True, slots=True)
class Operator:
    """Estructura de un operador"""
    name: str
    roles: tuple[str, ...]
    available: bool = True

    def can_handle(self, incident_type: str) -> bool:
        """Verificar si el operador puede manejar un tipo de incidente"""
        return incident_type in self.roles