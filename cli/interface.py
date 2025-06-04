"""
Interfaz de línea de comandos para el sistema de gestión de incidentes
"""

import os
from datetime import datetime, timedelta
from typing import Optional
import logging

from core.dispatcher import IncidentDispatcher
from incident.models import Incident

logger = logging.getLogger(__name__)


class IncidentManagerCLI:
    """Interfaz CLI para gestión de incidentes"""

    def __init__(self, dispatcher: IncidentDispatcher):
        self.dispatcher = dispatcher
        self.running = True

    def clear_screen(self):
        """Limpiar pantalla"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_header(self):
        """Mostrar encabezado del sistema"""
        print("=" * 60)
        print("🧠 SIMULADOR DE GESTIÓN DE INCIDENTES")
        print("   Sistema de Escalamiento y Flujos")
        print("=" * 60)
        print()

    def show_menu(self):
        """Mostrar menú principal"""
        print("📋 MENÚ PRINCIPAL")
        print("-" * 30)
        print("1. 📝 Registrar incidente")
        print("2. 📋 Ver incidentes pendientes")
        print("3. 👤 Asignar incidente a operador")
        print("4. ✅ Resolver incidente")
        print("5. ⚡ Escalar incidentes automáticamente")
        print("6. 📊 Ver historial")
        print("7. 🔍 Buscar incidentes")
        print("8. 👥 Gestionar operadores")
        print("9. 📈 Ver estadísticas")
        print("0. 🚪 Salir")
        print("-" * 30)

    def get_input(self, prompt: str, required: bool = True) -> Optional[str]:
        """Obtener entrada del usuario con validación"""
        while True:
            try:
                value = input(f"{prompt}: ").strip()
                if value or not required:
                    return value if value else None
                print("❌ Este campo es obligatorio")
            except (EOFError, KeyboardInterrupt):
                return None

    def get_choice(self, prompt: str, valid_choices: list) -> Optional[str]:
        """Obtener elección válida del usuario"""
        print(f"\n{prompt}")
        for i, choice in enumerate(valid_choices, 1):
            print(f"{i}. {choice}")

        while True:
            try:
                choice_input = input("Seleccione opción (número): ").strip()
                if not choice_input:
                    return None

                choice_num = int(choice_input)
                if 1 <= choice_num <= len(valid_choices):
                    return valid_choices[choice_num - 1]

                print(f"❌ Opción inválida. Ingrese número entre 1 y {len(valid_choices)}")

            except ValueError:
                print("❌ Ingrese un número válido")
            except (EOFError, KeyboardInterrupt):
                return None

    def register_incident(self):
        """Registrar nuevo incidente"""
        print("\n📝 REGISTRAR NUEVO INCIDENTE")
        print("-" * 35)

        # Obtener tipo
        incident_type = self.get_choice(
            "Tipo de incidente:",
            ["infrastructure", "security", "application"]
        )
        if not incident_type:
            print("❌ Operación cancelada")
            return

        # Obtener prioridad
        priority = self.get_choice(
            "Prioridad:",
            ["high", "medium", "low"]
        )
        if not priority:
            print("❌ Operación cancelada")
            return

        # Obtener descripción
        description = self.get_input("Descripción del incidente")
        if not description:
            print("❌ Operación cancelada")
            return

        # Registrar incidente
        with self.dispatcher.incident_session():
            incident_id = self.dispatcher.register_incident(incident_type, priority, description)

            if incident_id:
                print(f"\n✅ Incidente registrado exitosamente")
                print(f"   ID: {incident_id:03d}")
                print(f"   Tipo: {incident_type}")
                print(f"   Prioridad: {priority}")
                print(f"   Descripción: {description}")
            else:
                print("❌ Error al registrar el incidente")

    def show_pending_incidents(self):
        """Mostrar incidentes pendientes"""
        print("\n📋 INCIDENTES PENDIENTES")
        print("-" * 30)

        pending = self.dispatcher.get_pending_incidents()

        if not pending:
            print("✅ No hay incidentes pendientes")
            return

        print(f"Total de incidentes pendientes: {len(pending)}")
        print()

        for incident in pending:
            self._display_incident_summary(incident)

    def _display_incident_summary(self, incident: Incident):
        """Mostrar resumen de un incidente"""
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        type_icon = {"infrastructure": "🏗️", "security": "🔒", "application": "💻"}

        print(f"[{incident.id:03d}] {type_icon.get(incident.type, '📄')} {incident.type.title()}")
        print(f"      {priority_icon.get(incident.priority)} Prioridad: {incident.priority}")
        print(f"      📝 {incident.description[:60]}{'...' if len(incident.description) > 60 else ''}")
        print(f"      🕐 Creado: {incident.created_at.strftime('%d/%m/%Y %H:%M')}")
        if incident.assigned_to:
            print(f"      👤 Asignado a: {incident.assigned_to}")
        print(f"      📊 Estado: {incident.status}")
        print()

    def assign_incident(self):
        """Asignar incidente a operador"""
        print("\n👤 ASIGNAR INCIDENTE")
        print("-" * 25)

        # Mostrar incidentes pendientes
        pending = self.dispatcher.get_pending_incidents()
        if not pending:
            print("✅ No hay incidentes pendientes para asignar")
            return

        print("Incidentes disponibles:")
        for incident in pending[:10]:  # Mostrar solo los primeros 10
            print(f"  [{incident.id:03d}] {incident.type} - {incident.priority} - {incident.description[:40]}...")

        # Obtener ID del incidente
        incident_id_str = self.get_input("ID del incidente a asignar")
        if not incident_id_str:
            print("❌ Operación cancelada")
            return

        try:
            incident_id = int(incident_id_str)
        except ValueError:
            print("❌ ID inválido")
            return

        # Mostrar operadores disponibles
        operators = self.dispatcher.get_operators()
        available_operators = [name for name, op in operators.items() if op.available]

        if not available_operators:
            print("❌ No hay operadores disponibles")
            return

        print("\nOperadores disponibles:")
        for name in available_operators:
            operator = operators[name]
            print(f"  • {name} - Roles: {', '.join(operator.roles)}")

        # Obtener operador
        operator_name = self.get_input("Nombre del operador")
        if not operator_name:
            print("❌ Operación cancelada")
            return

        # Realizar asignación
        success = self.dispatcher.assign_incident(incident_id, operator_name)

        if success:
            print(f"✅ Incidente {incident_id:03d} asignado a {operator_name}")
        else:
            print("❌ Error al asignar incidente. Verifique ID, operador y permisos")

    def resolve_incident(self):
        """Resolver incidente"""
        print("\n✅ RESOLVER INCIDENTE")
        print("-" * 25)

        # Mostrar incidentes en progreso
        in_progress = list(self.dispatcher.get_incidents_by_status("in_progress"))
        pending = list(self.dispatcher.get_incidents_by_status("pending"))

        all_resolvable = in_progress + pending

        if not all_resolvable:
            print("✅ No hay incidentes para resolver")
            return

        print("Incidentes que se pueden resolver:")
        for incident in all_resolvable[:10]:
            print(f"  [{incident.id:03d}] {incident.type} - Asignado a: {incident.assigned_to or 'Sin asignar'}")

        # Obtener ID del incidente
        incident_id_str = self.get_input("ID del incidente a resolver")
        if not incident_id_str:
            print("❌ Operación cancelada")
            return

        try:
            incident_id = int(incident_id_str)
        except ValueError:
            print("❌ ID inválido")
            return

        # Resolver incidente
        success = self.dispatcher.resolve_incident(incident_id)

        if success:
            print(f"✅ Incidente {incident_id:03d} resuelto exitosamente")
        else:
            print("❌ Error al resolver incidente. Verifique que el ID sea válido")

    def auto_escalate(self):
        """Escalar incidentes automáticamente"""
        print("\n⚡ ESCALAMIENTO AUTOMÁTICO")
        print("-" * 35)

        print("Analizando incidentes para escalamiento...")
        escalated_count = self.dispatcher.auto_escalate_incidents()

        if escalated_count > 0:
            print(f"⚡ {escalated_count} incidente(s) escalado(s) automáticamente")
        else:
            print("✅ No hay incidentes que requieran escalamiento")

    def show_history(self):
        """Mostrar historial de operaciones"""
        print("\n📊 HISTORIAL DE OPERACIONES")
        print("-" * 35)

        history = self.dispatcher.get_history(20)  # Últimas 20 operaciones

        if not history:
            print("📋 No hay operaciones en el historial")
            return

        for entry in reversed(history):  # Mostrar más recientes primero
            timestamp = datetime.fromisoformat(entry['timestamp'])
            action_icons = {
                'created': '📝',
                'assigned': '👤',
                'resolved': '✅',
                'escalated': '⚡'
            }

            icon = action_icons.get(entry['action'], '📄')
            print(f"{icon} {timestamp.strftime('%d/%m %H:%M')} - "
                  f"ID:{entry['incident_id']:03d} - {entry['details']}")

    def search_incidents(self):
        """Buscar incidentes"""
        print("\n🔍 BUSCAR INCIDENTES")
        print("-" * 25)

        print("Criterios de búsqueda (presione Enter para omitir):")

        text = self.get_input("Texto en descripción", required=False)
        incident_type = self.get_choice("Tipo:", ["", "infrastructure", "security", "application"])
        operator = self.get_input("Operador asignado", required=False)
        status = self.get_choice("Estado:", ["", "pending", "in_progress", "resolved", "escalated"])

        days_str = self.get_input("Días hacia atrás (por defecto 30)", required=False)
        try:
            days_back = int(days_str) if days_str else 30
        except ValueError:
            days_back = 30

        # Realizar búsqueda
        results = self.dispatcher.search_incidents(
            text=text or "",
            incident_type=incident_type or "",
            operator=operator or "",
            status=status or "",
            days_back=days_back
        )

        print(f"\n🔍 Resultados de búsqueda: {len(results)} incidente(s)")
        print("-" * 40)

        if results:
            for incident in results[:20]:  # Mostrar máximo 20
                self._display_incident_summary(incident)
        else:
            print("No se encontraron incidentes con los criterios especificados")

    def manage_operators(self):
        """Gestionar operadores"""
        print("\n👥 GESTIÓN DE OPERADORES")
        print("-" * 30)

        while True:
            print("\nOpciones:")
            print("1. Ver operadores actuales")
            print("2. Agregar nuevo operador")
            print("3. Volver al menú principal")

            choice = self.get_input("Seleccione opción (1-3)")
            if not choice:
                break

            if choice == "1":
                self._show_operators()
            elif choice == "2":
                self._add_operator()
            elif choice == "3":
                break
            else:
                print("❌ Opción inválida")

    def _show_operators(self):
        """Mostrar lista de operadores"""
        operators = self.dispatcher.get_operators()

        print("\n👥 OPERADORES REGISTRADOS")
        print("-" * 30)

        for name, operator in operators.items():
            status_icon = "🟢" if operator.available else "🔴"
            print(f"{status_icon} {name}")
            print(f"     Roles: {', '.join(operator.roles)}")
            print()

    def _add_operator(self):
        """Agregar nuevo operador"""
        print("\n➕ AGREGAR OPERADOR")
        print("-" * 25)

        name = self.get_input("Nombre del operador")
        if not name:
            print("❌ Operación cancelada")
            return

        available_roles = ["admin", "security_analyst", "developer", "network_engineer", "system_admin", "app_support",
                           "incident_responder"]

        print("\nRoles disponibles:")
        for i, role in enumerate(available_roles, 1):
            print(f"{i}. {role}")

        roles_input = self.get_input("Números de roles separados por comas (ej: 1,3,5)")
        if not roles_input:
            print("❌ Operación cancelada")
            return

        try:
            role_indices = [int(x.strip()) - 1 for x in roles_input.split(",")]
            selected_roles = tuple(available_roles[i] for i in role_indices if 0 <= i < len(available_roles))

            if not selected_roles:
                print("❌ No se seleccionaron roles válidos")
                return

            success = self.dispatcher.add_operator(name, selected_roles)

            if success:
                print(f"✅ Operador {name} agregado con roles: {', '.join(selected_roles)}")
            else:
                print("❌ Error al agregar operador")

        except (ValueError, IndexError):
            print("❌ Formato de roles inválido")

    def show_statistics(self):
        """Mostrar estadísticas del sistema"""
        print("\n📈 ESTADÍSTICAS DEL SISTEMA")
        print("-" * 35)

        stats = self.dispatcher.get_statistics()

        print(f"📊 Resumen General:")
        print(f"   Total de incidentes: {stats.get('total', 0)}")
        print(f"   Operadores totales: {stats.get('operators_total', 0)}")
        print(f"   Operadores disponibles: {stats.get('operators_available', 0)}")
        print()

        print("📋 Por Estado:")
        statuses = ["pending", "in_progress", "resolved", "escalated"]
        for status in statuses:
            count = stats.get(f"status_{status}", 0)
            if count > 0:
                print(f"   {status.title()}: {count}")
        print()

        print("🎯 Por Prioridad:")
        priorities = ["high", "medium", "low"]
        for priority in priorities:
            count = stats.get(f"priority_{priority}", 0)
            if count > 0:
                print(f"   {priority.title()}: {count}")
        print()

        print("🏷️ Por Tipo:")
        types = ["infrastructure", "security", "application"]
        for incident_type in types:
            count = stats.get(f"type_{incident_type}", 0)
            if count > 0:
                print(f"   {incident_type.title()}: {count}")

    def run(self):
        """Ejecutar la interfaz CLI"""
        try:
            while self.running:
                self.clear_screen()
                self.show_header()

                # Escalamiento automático en cada ciclo
                escalated = self.dispatcher.auto_escalate_incidents()
                if escalated > 0:
                    print(f"⚡ {escalated} incidentes escalados automáticamente\n")

                self.show_menu()

                choice = self.get_input("Seleccione una opción")
                if not choice:
                    continue

                if choice == "1":
                    self.register_incident()
                elif choice == "2":
                    self.show_pending_incidents()
                elif choice == "3":
                    self.assign_incident()
                elif choice == "4":
                    self.resolve_incident()
                elif choice == "5":
                    self.auto_escalate()
                elif choice == "6":
                    self.show_history()
                elif choice == "7":
                    self.search_incidents()
                elif choice == "8":
                    self.manage_operators()
                elif choice == "9":
                    self.show_statistics()
                elif choice == "0":
                    print("\n👋 Guardando datos y cerrando sistema...")
                    with self.dispatcher.incident_session():
                        pass  # Fuerza el guardado
                    self.running = False
                else:
                    print("❌ Opción inválida")

                if self.running:
                    input("\nPresione Enter para continuar...")

        except KeyboardInterrupt:
            print("\n\n👋 Sistema cerrado por el usuario")
        except Exception as e:
            print(f"\n❌ Error en la interfaz: {e}")
            logger.error(f"Error en CLI: {e}", exc_info=True)
