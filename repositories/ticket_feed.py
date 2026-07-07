from database import get_connection
from repositories import notificaciones as notif_repo
from services.email import enviar_email_multiples
from templates.email_templates import template_comentario

# Agregar un registro al feed (comentario o actividad)
def agregar_comentario(id_ticket, tipo, id_usuario=None, detalle=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        INSERT INTO ticket_feed (id_ticket, tipo, id_usuario, detalle, fecha)
        VALUES (%s, %s, %s, %s, NOW())
    """

    # Obtener destinatarios del ticket
    cursor.execute(sql, (id_ticket, tipo, id_usuario, detalle))

    cursor.execute(
        """
        SELECT t.id_usuario, t.id_asignado, t.titulo,
               u.correo AS correo_creador
        FROM tickets t
        JOIN usuarios u ON t.id_usuario = u.id_usuario
        WHERE t.id_ticket = %s
        """,
        (id_ticket,)
    )
    ticket = cursor.fetchone()

    correo_asignado = None
    if ticket and ticket.get('id_asignado'):
        cursor.execute(
            "SELECT correo FROM usuarios WHERE id_usuario = %s",
            (ticket['id_asignado'],)
        )
        asignado = cursor.fetchone()
        correo_asignado = asignado['correo'] if asignado else None

    correo_autor = None
    cursor.execute(
        "SELECT correo FROM usuarios WHERE id_usuario = %s",
        (id_usuario,)
    )
    autor = cursor.fetchone()
    correo_autor = autor['correo'] if autor else None
    
    conn.commit()
    id_feed = cursor.lastrowid
    cursor.close()
    conn.close()
    
    # Notificar solo si es comentario
    if tipo == 'comentario' and ticket:
        destinatarios = list({ticket['id_usuario'], ticket.get('id_asignado')} - {None, id_usuario})
        notif_repo.notificar_usuarios(
            destinatarios, 'comentario_ticket',
            f"Nuevo comentario en ticket #{id_ticket}",
            referencia_id=id_ticket, referencia_tipo='ticket'
        )

    if tipo == 'comentario' and ticket:
        correos = [c for c in [ticket['correo_creador'], correo_asignado] if c and c != correo_autor]
        enviar_email_multiples(
            correos,
            f"Nuevo comentario en ticket #{id_ticket}",
            template_comentario(id_ticket, ticket['titulo'], detalle, str(id_usuario))
        )
    
    return id_feed


# Listar feed de un ticket (cronológico descendente)
def listar_feed(id_ticket):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT f.*, u.nombre AS nombre_usuario, u.apellido AS apellido_usuario
        FROM ticket_feed f
        LEFT JOIN usuarios u ON f.id_usuario = u.id_usuario
        WHERE f.id_ticket = %s
        ORDER BY f.fecha DESC
    """
    cursor.execute(sql, (id_ticket,))
    feed = cursor.fetchall()
    cursor.close()
    conn.close()
    return feed
