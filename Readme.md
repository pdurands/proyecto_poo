# Sistema de Gestión de Incidentes

Este proyecto es un sistema de gestión de incidentes diseñado para registrar, gestionar y escalar incidentes de manera eficiente. Incluye una interfaz de línea de comandos (CLI) para interactuar con el sistema y un módulo de persistencia para almacenar los datos de los incidentes.

## Características

- **Registro de incidentes**: Permite registrar nuevos incidentes con detalles como tipo, prioridad y descripción.
- **Gestión de estados**: Los incidentes pueden estar en diferentes estados: pendiente, en progreso, resuelto o escalado.
- **Escalamiento automático**: Los incidentes pueden ser escalados automáticamente según ciertas condiciones.
- **Historial y estadísticas**: Visualización del historial de incidentes y estadísticas por estado, prioridad y tipo.
- **Gestión de operadores**: Permite asignar incidentes a operadores disponibles.
- **Persistencia de datos**: Los incidentes se almacenan en un archivo JSON con soporte para backups automáticos.

## Estructura del Proyecto

- `cli/interface.py`: Implementa la interfaz de línea de comandos para interactuar con el sistema.
- `persistence/storage.py`: Módulo encargado de la persistencia de datos, incluyendo la creación de backups.
- `data/incidents.json`: Archivo donde se almacenan los incidentes registrados.
- `Readme.md`: Documentación del proyecto.

## Requisitos

- Python 3.8 o superior
- Dependencias especificadas en `requirements.txt` (si aplica)

## Uso

1. Clona este repositorio:
   ```bash
   git clone git@github.com:pdurands/proyecto_poo.git
   cd proyecto_poo
   python3 main.py