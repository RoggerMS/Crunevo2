from crunevo.models import Mission
from crunevo.extensions import db


def insertar_misiones():
    misiones = []

    # Diarias - subir apuntes
    for i in range(1, 11):
        misiones.append(
            Mission(
                code=f"subir_apuntes_{i}",
                description=f"Sube {i} apunte{'s' if i > 1 else ''} hoy",
                goal=i,
                credit_reward=2 + i,
                category="diaria",
            )
        )

    # Diarias - comentar
    for i in range(1, 6):
        misiones.append(
            Mission(
                code=f"comentar_{i}",
                description=f"Comenta en {i} publicación{'es' if i > 1 else ''}",
                goal=i,
                credit_reward=1 + i,
                category="diaria",
            )
        )

    # Semanales - recibir likes
    for i in [5, 10, 15, 20]:
        misiones.append(
            Mission(
                code=f"likes_{i}",
                description=f"Recibe {i} likes esta semana",
                goal=i,
                credit_reward=2 + (i // 2),
                category="semanal",
            )
        )

    # Especiales - comprar productos
    for i in range(1, 6):
        misiones.append(
            Mission(
                code=f"comprar_producto_{i}",
                description=f"Compra {i} producto{'s' if i > 1 else ''} en la tienda",
                goal=i,
                credit_reward=10 * i,
                category="especial",
            )
        )

    # Logros únicos
    logros = [
        ("referido_1", "Invita a 1 amigo y que valide su cuenta", 1, 50),
        ("referido_5", "Invita a 5 amigos activos", 5, 100),
        ("referido_10", "Invita a 10 amigos activos", 10, 300),
        ("referido_20", "Invita a 20 amigos activos", 20, 600),
        (
            "referido_maraton",
            "Invita a 5 amigos activos en una semana",
            5,
            500,
        ),
        ("primer_apunte", "Sube tu primer apunte", 1, 20),
        ("primer_like", "Recibe tu primer like", 1, 10),
        ("maraton_apuntes", "Sube 10 apuntes en 1 día", 10, 80),
    ]
    for code, desc, goal, reward in logros:
        misiones.append(
            Mission(
                code=code,
                description=desc,
                goal=goal,
                credit_reward=reward,
                category="logro",
            )
        )

    # Insertar en base de datos
    for m in misiones:
        if not Mission.query.filter_by(code=m.code).first():
            db.session.add(m)
    db.session.commit()
    print("✅ Misiones insertadas correctamente.")


# Ejecutar manualmente
if __name__ == "__main__":
    insertar_misiones()
