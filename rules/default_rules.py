"""
Reglas por defecto del sistema
"""

from typing import Dict, Set, List
from incident.models import Operator

def get_default_rules() -> Dict[str, Set[str]]:
    """Obtener reglas por defecto: tipo de incidente -> roles permitidos"""
    return {
        "infrastructure": {"admin", "network_engineer", "system_admin"},
        "security": {"security_analyst", "admin", "incident_responder"},
        "application": {"developer", "app_support", "admin"}
    }

def get_default_operators() -> List[Operator]:
    """Obtener operadores por defecto"""
    return [
        Operator(name="carlos", roles=("admin", "system_admin"), available=True),
        Operator(name="ana", roles=("security_analyst", "incident_responder"), available=True),
        Operator(name="miguel", roles=("developer", "app_support"), available=True),
        Operator(name="sofia", roles=("network_engineer", "system_admin"), available=True),
        Operator(name="admin", roles=("admin", "security_analyst", "developer", "network_engineer"), available=True),
    ]