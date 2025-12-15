# SuperSID Pro

SuperSID Pro es un sistema de monitoreo de señales VLF (Very Low Frequency) con visualización en tiempo real a través de una interfaz web moderna.

## Tabla de contenidos

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Ejecutar el servidor](#ejecutar-el-servidor)
- [Acceso a la interfaz web](#acceso-a-la-interfaz-web)
- [Configuración de entrada de audio](#configuración-de-entrada-de-audio)
- [Simulación vs. audio real](#simulación-vs-audio-real)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Desarrollo y personalización](#desarrollo-y-personalización)
- [Notas útiles y resolución de problemas](#notas-útiles-y-resolución-de-problemas)
- [Licencia](#licencia)

---

## Características

- Captura y visualización de señales VLF con 27 estaciones internacionales.
- Gráficos individuales y resumen general en tiempo real.
- Datos de Space Weather integrados.
- Selección de dispositivo de audio desde la interfaz web.
- Sistema de simulación integrado para pruebas sin hardware.
- Streaming y dashboard moderno vía FastAPI y WebSockets.

---

## Requisitos

- Python 3.8 o superior.
- Sistema Linux recomendado con acceso a entrada de audio (placa de sonido o tarjeta externa).
- Navegador web moderno (Chrome, Edge, Firefox).
- Dependencias Python en `requirements.txt`.

---

## Instalación

1. Clona el repositorio:
    ```bash
    git clone https://github.com/tuusuario/SuperSID_Pro.git
    cd SuperSID_Pro
    ```

2. (Opcional) Crea y activa un entorno virtual:
    ```bash
    python3 -m venv SuperSID_Pro
    source SuperSID_Pro/bin/activate
    ```

3. Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```

---

## Ejecutar el servidor

```bash
python3 web_server.py --port 8080 --debug
```

- El servidor mostrará la URL, por defecto será:  
  `http://localhost:8080`

---

## Acceso a la interfaz web

1. Abre tu navegador y visita:  
   `http://localhost:8080`

2. La primera vez aparecerá la pantalla de configuración.

---

## Configuración de entrada de audio

1. Ve a "SETTINGS" o "Setup" en la interfaz.
2. Selecciona el dispositivo de audio correcto (placa de sonido/MIC).
   - Puedes ver el nombre del dispositivo, sample rate y buffer.
3. Guarda la configuración y recarga el monitoreo (STOP y START).
4. Si el sistema está tomando datos reales:
   - Verás mensajes como  
     `Starting real audio capture from device X`
   - Las gráficas mostrarán señales "ruidosas" y cambiantes.

---

## Simulación vs audio real

- **Simulación:**  
  El sistema genera ondas artificiales, suaves y predecibles.  
  Es útil para pruebas, pero no representa el entorno físico.

- **Audio real:**  
  El sistema utiliza la señal digitalizada proveniente de una placa de sonido (idealmente conectada a una antena VLF).
  Cambios físicos (desconexión/conexión, manipular la línea/micrófono) se reflejan en los gráficos.

Por defecto, el sistema usa simulación si no hay un dispositivo de audio configurado.

---

## Estructura del proyecto

```
SuperSID_Pro/
│
├── src/
│   ├── web/
│   │   ├── api/                # Backend API (FastAPI)
│   │   ├── static/             # Archivos web: JS, CSS, imágenes
│   │   ├── templates/          # Archivos HTML (Jinja2)
│   │
│   ├── core/                   # Lógica principal: adquisición, procesado, audio, etc
│   ├── data/                   # Almacenamiento temporal y reportes
│
├── config/                     # Configuración por defecto y personalizada
├── requirements.txt            # Dependencias requeridas
├── web_server.py               # Script principal del servidor
└── README.md                   # Esta documentación
```

---

## Desarrollo y personalización

- **Backend (API y simulación):**
  - Ubicado en `src/web/api/vlf_api.py`.
  - Modificar el bucle de simulación, agregar nuevas estaciones, gestionar la entrada de audio.
  - El método `start_real_audio_capture(device_index, sample_rate, buffer_size)` activa la adquisición real usando la placa seleccionada.

- **Frontend (dashboard):**
  - Todo el JS está en `src/web/static/js/dashboard.js`.
  - Modificar apariencia, agregar nuevos gráficos, cambiar estilos en `src/web/static/css/dashboard.css`.
  - El motor gráfico es [Chart.js](https://www.chartjs.org/).

- **Agregar nuevas estaciones:**
  - Modifica el archivo de configuración (`config/default_config.json`) para agregar/editar estaciones.
  - Personaliza frecuencias, nombres, etc.

- **WebSockets:**
  - Los datos se envían en tiempo real desde backend a frontend por `/ws`.
  - Puedes inspeccionar lo que envía el backend usando herramientas de desarrollador del navegador, pestaña "Network" > "WS".

- **Workflow de desarrollo:**
  - Realiza cambios en el backend o frontend.
  - Reinicia el servidor y recarga la página web (Ctrl+Shift+R).

---

## Notas útiles y resolución de problemas

- Si ves ondas perfectamente suaves suele ser la simulación, revisa configuración de audio.
- Si el navegador muestra “Internal Server Error” puede ser:
  - Una plantilla faltante.
  - Error de configuración, verifica logs en la terminal.
- Mensajes como "cannot find card '0'" en la terminal indican problemas de detección de la placa por ALSA (Linux). Asegúrate que tu dispositivo está conectado y habilitado.
- Puedes listar dispositivos de audio disponibles en la página de settings.
- Para depurar problemas en el frontend, usa las DevTools del navegador (F12).
- Consultar los logs del backend para más detalles sobre errores.

---

## Licencia

Este proyecto es software libre. Consulta el archivo `LICENSE` para más detalles.