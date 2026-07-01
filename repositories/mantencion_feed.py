from database import get_connection
from typing import Optional
from repositories import notificaciones as notif_repo


def agregar_evento(id_mantencion: int, id_usuario: int, tipo: str, detalle: str):
    """Registra un evento en el feed de la mantención."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO mantencion_feed (id_mantencion, id_usuario, tipo, detalle, fecha)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        (id_mantencion, id_usuario, tipo, detalle),
    )

    # Obtener destinatarios de la mantención
    cursor.execute(
        "SELECT id_usuario_solicitante, id_usuario_asignado FROM mantenciones WHERE id_mantencion = %s",
        (id_mantencion,)
    )
    mantencion = cursor.fetchone()

    conn.commit()
    id_feed = cursor.lastrowid
    cursor.close()
    conn.close()

    # Notificar solo si es comentario
    if tipo == 'comentario' and mantencion:
        destinatarios = list(
            {mantencion['id_usuario_solicitante'], mantencion.get('id_usuario_asignado')} - {None, id_usuario}
        )
        notif_repo.notificar_usuarios(
            destinatarios, 'comentario_mantencion',
            f"Nuevo comentario en mantención #{id_mantencion}",
            referencia_id=id_mantencion, referencia_tipo='mantencion'
        )

    return id_feed


def listar_feed(id_mantencion: int):
    """Retorna el feed completo de una mantención con datos del usuario."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            f.*,
            u.nombre AS nombre_usuario,
            u.apellido AS apellido_usuario
        FROM mantencion_feed f
        JOIN usuarios u ON f.id_usuario = u.id_usuario
        WHERE f.id_mantencion = %s
        ORDER BY f.fecha ASC
        """,
        (id_mantencion,),
    )
    feed = cursor.fetchall()
    # Serializar datetime a string
    for item in feed:
        if item.get('fecha') and not isinstance(item['fecha'], str):
            item['fecha'] = str(item['fecha'])
    cursor.close()
    conn.close()
    return feed