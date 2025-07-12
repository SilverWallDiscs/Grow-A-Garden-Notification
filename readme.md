# Grow A Garden Store Monitor

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)
![WebSockets](https://img.shields.io/badge/WebSockets-supported-yellow.svg)

Aplicación de monitorización de la tienda del juego "Grow A Garden" que muestra los artículos disponibles, su calidad y stock, con notificaciones para artículos especiales.

## Características

- Conexión en tiempo real vía WebSocket a la tienda del juego
- Interfaz gráfica moderna con PyQt6
- Sistema de notificaciones para artículos especiales (como Prismatic)
- Temporizador para próximas actualizaciones
- Clasificación por calidad de artículos con colores distintivos
- Diseño sin bordes con capacidad de arrastrar la ventana

## Requisitos

- Python 3.8+
- Dependencias (instalar con `pip install -r requirements.txt`):
  ```
  PyQt6
  websockets
  win10toast
  ```

## Instalación

1. Clona el repositorio o descarga los archivos
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta la aplicación:
   ```bash
   python store_monitor.py
   ```

## Uso

- La aplicación se conecta automáticamente al servidor del juego
- Muestra una tabla con todos los artículos disponibles, organizados por categoría
- Los artículos se colorean según su rareza
- Cuando aparece un artículo "Prismatic", se mostrará una notificación y sonará un tono
- El temporizador superior muestra el tiempo restante para la próxima actualización

## Personalización

Puedes modificar los siguientes aspectos editando el código:

- `QUALITY_COLORS`: Cambia los colores asociados a cada calidad
- `ITEM_QUALITIES`: Añade nuevos artículos o modifica sus calidades
- `update_interval`: Ajusta el intervalo entre actualizaciones (por defecto 5 minutos y 3 segundos)

## Notas

- Esta aplicación está diseñada para Windows (usa `winsound` y `win10toast`)
- Para otros sistemas operativos, sería necesario adaptar las notificaciones y sonidos

## Autor

SilverWallDisc

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.