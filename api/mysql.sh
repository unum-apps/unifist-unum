#!/bin/sh -e
python - <<PY
import os
import socket
import time

host = os.environ["MYSQL_HOST"]
port = int(os.environ["MYSQL_PORT"])

while True:
    try:
        socket.create_connection((host, port), timeout=1).close()
        break
    except OSError:
        time.sleep(1)

print("MySQL ready")
PY
