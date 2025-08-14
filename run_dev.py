#!/usr/bin/env python3
"""
Script de desarrollo para ejecutar Crunevo localmente sin problemas de SSL.
Este script configura automáticamente las variables de entorno necesarias
para deshabilitar HTTPS enforcement en desarrollo local.
"""

import os
import sys
import subprocess


def main():
    print("🚀 Iniciando Crunevo en modo desarrollo...")

    # Configurar variables de entorno para desarrollo local
    env_vars = {
        "ENABLE_TALISMAN": "0",  # Deshabilitar Talisman (HTTPS enforcement)
        "FORCE_HTTPS": "0",  # Deshabilitar redirección HTTPS
        "FLASK_ENV": "development",
        "FLASK_DEBUG": "1",
    }

    # Aplicar variables de entorno
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ {key} = {value}")

    print("\n📡 Iniciando servidor Flask en http://localhost:5000")
    print("🔓 SSL/HTTPS deshabilitado para desarrollo local")
    print("⚠️  NOTA: Estas configuraciones son solo para desarrollo local")
    print("   En producción, Talisman y HTTPS siguen activos.\n")

    try:
        # Ejecutar Flask
        subprocess.run(
            [
                sys.executable,
                "-m",
                "flask",
                "run",
                "--host=0.0.0.0",
                "--port=5000",
                "--debug",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar Flask: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
