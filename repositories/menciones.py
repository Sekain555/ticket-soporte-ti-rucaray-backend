from database import get_connection
from typing import Optional


def registrar_mencion(
    id_usuario: int,
    referencia_id: int,
    referencia_tipo: str,
    id_feed: int,
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO menciones (id_usuario, referencia_id, referencia_tipo, id_feed, fecha)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        (id_usuario, referencia_id, referencia_tipo, id_feed),
    )
    conn.commit()
    cursor.close()
    conn.close()


def registrar_menciones(
    id_usuarios: list,
    referencia_id: int,
    referencia_tipo: str,
    id_feed: int,
):
    """Registra múltiples menciones de una sola vez."""
    if not id_usuarios:
        return
    conn = get_connection()
    cursor = conn.cursor()
    valores = [
        (id_u, referencia_id, referencia_tipo, id_feed)
        for id_u in id_usuarios
    ]
    cursor.executemany(
        """
        INSERT INTO menciones (id_usuario, referencia_id, referencia_tipo, id_feed, fecha)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        valores,
    )
    conn.commit()
    cursor.close()
    conn.close()


def obtener_mencionados(referencia_id: int, referencia_tipo: str) -> list:
    """Retorna los id_usuario mencionados en un ticket o mantención."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT DISTINCT id_usuario FROM menciones
        WHERE referencia_id = %s AND referencia_tipo = %s
        """,
        (referencia_id, referencia_tipo),
    )
    result = [r['id_usuario'] for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return result


def es_mencionado(id_usuario: int, referencia_id: int, referencia_tipo: str) -> bool:
    """Verifica si un usuario fue mencionado en un ticket o mantención."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT COUNT(*) AS total FROM menciones
        WHERE id_usuario = %s AND referencia_id = %s AND referencia_tipo = %s
        """,
        (id_usuario, referencia_id, referencia_tipo),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row['total'] > 0 if row else False