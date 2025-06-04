"""
Despachador central del sistema de gestión de incidentes
"""

from collections import deque, defaultdict
from datetime import datetime
from typing import Optional, Dict, Set, List, Iterator
from contextlib import contextmanager
import logging

from incident.models import Incident, Operator
from incident.filters import IncidentFilter
from core.escalator import IncidentEscalator, CompositeEscalation, TimeBasedEscalation, PriorityBasedEscalation
from core.validator import IncidentValidator, log_operation, validate_input
from rules.default_rules import get_default_rules, get_default_operators
from persistence.storage import StorageManager

logger = logging.getLogger(__name__)


class IncidentDispatcher:
    """Despachador central para gestión de incidentes"""

    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager
        self.incidents: Dict[int, Incident] = {}
        self.pending_queue = deque()  # Cola por prioridad
        self.operators: Dict[str, Operator] = {}
        self.type_to_roles: Dict[str, Set[str]] = defaultdict(set)
        self.history: List[Dict] = []
        self.next_id = 1

        # Componentes
        self.escalator = IncidentEscalator(
            CompositeEscalation(
                TimeBasedEscalation(30),
                PriorityBasedEscalation(True)
            )
        )

        # Inicializar sistema
        self._initialize_system()

    def _initialize_system(self):
        """Inicializar reglas y operadores por defecto"""
        try:
            # Cargar datos persistidos
            self._load_persisted_data()

            # Cargar reglas por defecto
            self.type_to_roles.update(get_default_rules())

            # Cargar operadores por defecto si no hay ninguno
            if not self.operators:
                for operator in get_default_operators():
                    self.operators[operator.name] = operator

            logger.info(f"Sistema inicializado con {len(self.operators)} operadores")

        except Exception as e:
            logger.error(f"Error inicializando sistema: {e}")
            # Continuar con configuración por defecto
            self.type_to_roles.update(get_default_rules())
            for operator in get_default_operators():
                self.operators[operator.name] = operator

    def _load_persisted_data(self):
        """Cargar datos desde almacenamiento"""
        try:
            data = self.storage.load_incidents()
            for incident_data in data:
                incident = Incident.from_dict(incident_data)
                self.incidents[incident.id] = incident
                if incident.status == "pending":
                    self._add_to_queue(incident)
                self.next_id = max(self.next_id, incident.id + 1)

            logger.info(f"Cargados {len(self.incidents)} incidentes desde almacenamiento")
        except Exception as e:
            logger.warning(f"No se pudieron cargar datos persistidos: {e}")

    def _add_to_queue(self, incident: Incident):
        """Agregar incidente a la cola según prioridad"""
        if incident.priority == "high":
            self.pending_queue.appendleft(incident)  # Alta prioridad al inicio
        else:
            self.pending_queue.append(incident)

    @contextmanager
    def incident_session(self):
        """Contexto para operaciones con incidentes"""
        logger.info("Iniciando sesión de incidentes")
        try:
            yield self
        except Exception as e:
            logger.error(f"Error en sesión de incidentes: {e}")
            raise
        finally:
            self._save_data()
            logger.info("Sesión de incidentes finalizada")

    def _save_data(self):
        """Guardar datos al almacenamiento"""
        try:
            incidents_data = [incident.to_dict() for incident in self.incidents.values()]
            self.storage.save_incidents(incidents_data)
            #logger.info("Datos guardados exitosamente")
        except Exception as e:
            logger.error(f"Error guardando datos: {e}")

    @log_operation("registro_incidente")
    @validate_input(lambda x: isinstance(x, str) and x.strip(), "Tipo de incidente inválido")
    def register_incident(self, incident_type: str, priority: str, description: str) -> Optional[int]:
        """Registrar un nuevo incidente"""
        try:
            # Validar datos
            errors = IncidentValidator.validate_all_incident_data(incident_type, priority, description)
            if errors:
                logger.error(f"Errores de validación: {'; '.join(errors)}")
                raise ValueError(f"Datos inválidos: {'; '.join(errors)}")

            # Crear incidente
            incident = Incident(
                id=self.next_id,
                type=incident_type,
                priority=priority,
                description=description.strip(),
                created_at=datetime.now(),
                assigned_to=None,
                status="pending"
            )

            # Almacenar
            self.incidents[incident.id] = incident
            self._add_to_queue(incident)
            self.next_id += 1

            # Registrar en historial
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'created',
                'incident_id': incident.id,
                'details': f"Creado: {incident_type} - {priority}"
            })

            #logger.info(f"Incidente {incident.id} registrado exitosamente")
            return incident.id

        except Exception as e:
            logger.error(f"Error registrando incidente: {e}")
            return None

    def get_pending_incidents(self) -> List[Incident]:
        """Obtener lista de incidentes pendientes por prioridad"""
        return list(self.pending_queue)

    def get_incidents_by_status(self, status: str) -> Iterator[Incident]:
        """Obtener incidentes por estado usando generador"""
        for incident in self.incidents.values():
            if incident.status == status:
                yield incident

    @log_operation("asignacion_incidente")
    def assign_incident(self, incident_id: int, operator_name: str) -> bool:
        """Asignar incidente a operador"""
        try:
            # Validar incidente existe
            if incident_id not in self.incidents:
                logger.warning(f"Incidente {incident_id} no encontrado")
                return False

            incident = self.incidents[incident_id]

            # Validar estado
            if incident.status != "pending":
                logger.warning(f"Incidente {incident_id} no está pendiente")
                return False

            # Validar operador existe y está disponible
            if operator_name not in self.operators:
                logger.warning(f"Operador {operator_name} no encontrado")
                return False

            operator = self.operators[operator_name]
            if not operator.available:
                logger.warning(f"Operador {operator_name} no disponible")
                return False

            # Validar permisos
            if not operator.can_handle(incident.type):
                logger.warning(f"Operador {operator_name} no puede manejar tipo {incident.type}")
                return False

            # Realizar asignación
            updated_incident = incident.with_assignment(operator_name)
            self.incidents[incident_id] = updated_incident

            # Remover de cola pendientes
            self.pending_queue = deque(inc for inc in self.pending_queue if inc.id != incident_id)

            # Registrar en historial
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'assigned',
                'incident_id': incident_id,
                'operator': operator_name,
                'details': f"Asignado a {operator_name}"
            })

            logger.info(f"Incidente {incident_id} asignado a {operator_name}")
            return True

        except Exception as e:
            logger.error(f"Error asignando incidente {incident_id}: {e}")
            return False

    @log_operation("resolucion_incidente")
    def resolve_incident(self, incident_id: int) -> bool:
        """Resolver un incidente"""
        try:
            if incident_id not in self.incidents:
                logger.warning(f"Incidente {incident_id} no encontrado")
                return False

            incident = self.incidents[incident_id]

            if incident.status not in ["pending", "in_progress"]:
                logger.warning(f"Incidente {incident_id} no se puede resolver (estado: {incident.status})")
                return False

            # Actualizar estado
            resolved_incident = incident.with_status("resolved")
            self.incidents[incident_id] = resolved_incident

            # Remover de cola si estaba pendiente
            self.pending_queue = deque(inc for inc in self.pending_queue if inc.id != incident_id)

            # Registrar en historial
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'resolved',
                'incident_id': incident_id,
                'operator': incident.assigned_to,
                'details': f"Resuelto por {incident.assigned_to or 'sistema'}"
            })

            logger.info(f"Incidente {incident_id} resuelto")
            return True

        except Exception as e:
            logger.error(f"Error resolviendo incidente {incident_id}: {e}")
            return False

    def auto_escalate_incidents(self) -> int:
        """Escalar automáticamente incidentes según reglas"""
        escalated_count = 0
        try:
            # Encontrar incidentes para escalar
            pending_incidents = list(self.get_incidents_by_status("pending")) + \
                                list(self.get_incidents_by_status("in_progress"))

            for incident in self.escalator.find_escalatable_incidents(pending_incidents):
                escalated_incident = self.escalator.escalate_incident(incident)
                self.incidents[incident.id] = escalated_incident

                # Remover de cola pendientes
                self.pending_queue = deque(inc for inc in self.pending_queue if inc.id != incident.id)

                # Registrar en historial
                self.history.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'escalated',
                    'incident_id': incident.id,
                    'details': 'Escalado automáticamente por tiempo'
                })

                escalated_count += 1

            if escalated_count > 0:
                logger.info(f"Escalados {escalated_count} incidentes automáticamente")

            return escalated_count

        except Exception as e:
            logger.error(f"Error en escalamiento automático: {e}")
            return 0

    def search_incidents(self, text: str = "", incident_type: str = "",
                         operator: str = "", status: str = "",
                         days_back: int = 30) -> List[Incident]:
        """Buscar incidentes con múltiples criterios"""
        try:
            incidents = self.incidents.values()

            # Aplicar filtros
            if text:
                incidents = IncidentFilter.by_text(incidents, text)

            if incident_type:
                incidents = IncidentFilter.by_type(incidents, incident_type)

            if operator:
                incidents = IncidentFilter.by_operator(incidents, operator)

            if status:
                incidents = IncidentFilter.by_status(incidents, status)

            if days_back > 0:
                start_date = datetime.now() - timedelta(days=days_back)
                incidents = IncidentFilter.by_date_range(incidents, start_date=start_date)

            return list(incidents)

        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Obtener historial de operaciones"""
        return self.history[-limit:]

    def get_operators(self) -> Dict[str, Operator]:
        """Obtener diccionario de operadores"""
        return self.operators.copy()

    def add_operator(self, name: str, roles: tuple[str, ...]) -> bool:
        """Agregar nuevo operador"""
        try:
            if not IncidentValidator.validate_operator_name(name):
                logger.warning(f"Nombre de operador inválido: {name}")
                return False

            operator = Operator(name=name.strip(), roles=roles)
            self.operators[operator.name] = operator
            logger.info(f"Operador {name} agregado con roles: {', '.join(roles)}")
            return True

        except Exception as e:
            logger.error(f"Error agregando operador: {e}")
            return False

    def get_statistics(self) -> Dict[str, int]:
        """Obtener estadísticas del sistema"""
        stats = defaultdict(int)

        for incident in self.incidents.values():
            stats[f"total"] += 1
            stats[f"status_{incident.status}"] += 1
            stats[f"priority_{incident.priority}"] += 1
            stats[f"type_{incident.type}"] += 1

        stats["operators_total"] = len(self.operators)
        stats["operators_available"] = sum(1 for op in self.operators.values() if op.available)

        return dict(stats)