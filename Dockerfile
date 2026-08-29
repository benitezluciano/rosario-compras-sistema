FROM python:3.11-slim-bookworm

# Evitar prompts interactivos durante la instalación de paquetes
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema para PyQt6, entorno gráfico virtual X11 y noVNC
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    autocutsel \
    x11-xkb-utils \
    xclip \
    dos2unix \
    procps \
    libgl1 \
    libegl1 \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libx11-xcb1 \
    libxcb1 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libfontconfig1 \
    libdbus-1-3 \
    libsm6 \
    libice6 \
    && rm -rf /var/lib/apt/lists/*

# Crear enlace simbólico para que noVNC sirva directamente en /vnc.html o /
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html || true

WORKDIR /app

# Copiar requerimientos e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente de la aplicación
COPY . .

# Convertir saltos de línea de Windows (CRLF) a Linux (LF) y dar permisos de ejecución
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Exponer el puerto Web noVNC
EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
