#!/bin/bash
set -e

echo "=== INICIANDO ENTORNO GRÁFICO VIRTUAL (noVNC / Xvfb) ==="

export DISPLAY=:99
export RESOLUTION=${RESOLUTION:-1280x800x24}

# 1. Iniciar servidor X virtual Xvfb
echo "Iniciando Xvfb en display :99 con resolución $RESOLUTION..."
Xvfb :99 -screen 0 $RESOLUTION -ac +extension GLX +render -noreset &
sleep 1

# 2. Iniciar gestor de ventanas ligero Fluxbox
echo "Iniciando Fluxbox Window Manager..."
fluxbox &
sleep 1

# 3. Iniciar servidor VNC sin contraseña
echo "Iniciando x11vnc..."
x11vnc -display :99 -nopw -listen localhost -xkb -forever -shared -bg -rfbport 5900
sleep 1

# 4. Iniciar bridge WebSockets noVNC en puerto 8080
echo "Iniciando noVNC Web en puerto 8080..."
websockify --web /usr/share/novnc 8080 localhost:5900 &
sleep 1

# 5. Asegurar inicialización de base de datos
if [ ! -f "/app/database.db" ]; then
    echo "Inicializando y poblando base de datos database.db..."
    python seeds/seed_db.py
fi

echo "=========================================================="
echo " Rosario Compras iniciado con éxito en Docker!"
echo " Abre tu navegador en: http://localhost:8080/vnc.html"
echo " (o http://localhost:8080)"
echo "=========================================================="

# 6. Lanzar la aplicación principal PyQt6
exec python main.py
