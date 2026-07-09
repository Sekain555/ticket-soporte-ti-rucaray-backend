BASE_URL = "http://192.168.4.246:2000"

def _base_template(contenido: str) -> str:
    return f"""
    <html>
    <body style="margin:0; padding:0; background:#f4f4f4; font-family: Arial, sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4; padding: 32px 0;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background:#1a1a1a; border-radius:12px; overflow:hidden;">
              
              <!-- Cabecera -->
              <tr>
                <td style="background:#1a56db; padding:20px 32px;">
                  <p style="margin:0; color:#ffffff; font-size:11px; letter-spacing:1px;">SOPORTE TI — RUCARAY</p>
                  <p style="margin:4px 0 0; color:#ffffff; font-size:20px; font-weight:bold;">Sistema de Tickets</p>
                </td>
              </tr>

              <!-- Contenido -->
              <tr>
                <td style="padding:32px;">
                  {contenido}
                </td>
              </tr>

              <!-- Pie -->
              <tr>
                <td style="padding:16px 32px; border-top:1px solid #2a2a2a;">
                  <p style="margin:0; color:#6b7280; font-size:11px;">
                    Este es un correo automático del Sistema de Tickets Rucaray — STR. No responder directamente.
                  </p>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

def _boton(texto: str, url: str) -> str:
    return f"""
    <a href="{url}" style="display:inline-block; margin-top:24px; padding:12px 24px;
       background:#1a56db; color:#ffffff; text-decoration:none; border-radius:8px;
       font-size:14px; font-weight:bold;">{texto}</a>
    """

def template_ticket_creado(id_ticket: int, titulo: str, creador: str, prioridad: str) -> str:
    url = f"{BASE_URL}/detalle-ticket/{id_ticket}"
    contenido = f"""
    <p style="color:#9ca3af; font-size:13px; margin:0 0 8px;">NUEVO TICKET</p>
    <h2 style="color:#ffffff; margin:0 0 24px; font-size:18px;">#{id_ticket} — {titulo}</h2>
    <table cellpadding="0" cellspacing="0" style="width:100%;">
      <tr>
        <td style="color:#9ca3af; font-size:13px; padding:6px 0; width:140px;">Reportado por</td>
        <td style="color:#ffffff; font-size:13px; padding:6px 0;">{creador}</td>
      </tr>
      <tr>
        <td style="color:#9ca3af; font-size:13px; padding:6px 0;">Prioridad</td>
        <td style="color:#ffffff; font-size:13px; padding:6px 0;">{prioridad.capitalize()}</td>
      </tr>
    </table>
    {_boton('Ver ticket', url)}
    """
    return _base_template(contenido)


def template_ticket_asignado(id_ticket: int, titulo: str, asignado_a: str) -> str:
    url = f"{BASE_URL}/detalle-ticket/{id_ticket}"
    contenido = f"""
    <p style="color:#9ca3af; font-size:13px; margin:0 0 8px;">TICKET ASIGNADO</p>
    <h2 style="color:#ffffff; margin:0 0 24px; font-size:18px;">#{id_ticket} — {titulo}</h2>
    <p style="color:#d1d5db; font-size:14px;">Se te ha asignado el siguiente ticket de soporte.</p>
    <table cellpadding="0" cellspacing="0" style="width:100%;">
      <tr>
        <td style="color:#9ca3af; font-size:13px; padding:6px 0; width:140px;">Asignado a</td>
        <td style="color:#ffffff; font-size:13px; padding:6px 0;">{asignado_a}</td>
      </tr>
    </table>
    {_boton('Ver ticket', url)}
    """
    return _base_template(contenido)


def template_ticket_cerrado(id_ticket: int, titulo: str, resultado_sla: str) -> str:
    url = f"{BASE_URL}/detalle-ticket/{id_ticket}"
    sla_texto = {
        'dentro_plazo': '✅ Resuelto dentro del plazo SLA',
        'fuera_plazo': '⚠️ Resuelto fuera del plazo SLA',
        'sin_sla': 'Sin SLA asignado'
    }.get(resultado_sla, '')
    contenido = f"""
    <p style="color:#9ca3af; font-size:13px; margin:0 0 8px;">TICKET CERRADO</p>
    <h2 style="color:#ffffff; margin:0 0 24px; font-size:18px;">#{id_ticket} — {titulo}</h2>
    <p style="color:#d1d5db; font-size:14px;">Tu solicitud de soporte ha sido resuelta.</p>
    <p style="color:#d1d5db; font-size:14px;">{sla_texto}</p>
    {_boton('Ver ticket', url)}
    """
    return _base_template(contenido)


def template_comentario(id_ticket: int, titulo: str, comentario: str, autor: str) -> str:
    url = f"{BASE_URL}/detalle-ticket/{id_ticket}"
    contenido = f"""
    <p style="color:#9ca3af; font-size:13px; margin:0 0 8px;">NUEVO COMENTARIO</p>
    <h2 style="color:#ffffff; margin:0 0 24px; font-size:18px;">#{id_ticket} — {titulo}</h2>
    <div style="background:#2a2a2a; border-radius:8px; padding:16px; margin:16px 0;">
      <p style="color:#9ca3af; font-size:12px; margin:0 0 8px;">{autor}</p>
      <p style="color:#d1d5db; font-size:14px; margin:0;">{comentario}</p>
    </div>
    {_boton('Ver ticket', url)}
    """
    return _base_template(contenido)


def template_sla_vencido(id_ticket: int, titulo: str, fecha_limite: str) -> str:
    url = f"{BASE_URL}/detalle-ticket/{id_ticket}"
    contenido = f"""
    <p style="color:#ef4444; font-size:13px; margin:0 0 8px;">⚠️ SLA VENCIDO</p>
    <h2 style="color:#ffffff; margin:0 0 24px; font-size:18px;">#{id_ticket} — {titulo}</h2>
    <p style="color:#d1d5db; font-size:14px;">Este ticket ha superado su fecha límite de resolución.</p>
    <table cellpadding="0" cellspacing="0" style="width:100%;">
      <tr>
        <td style="color:#9ca3af; font-size:13px; padding:6px 0; width:140px;">Fecha límite</td>
        <td style="color:#ef4444; font-size:13px; padding:6px 0;">{fecha_limite}</td>
      </tr>
    </table>
    {_boton('Ver ticket', url)}
    """
    return _base_template(contenido)


def template_mantencion(id_mantencion: int, titulo: str, nuevo_estado: str, fecha: str, hora_inicio: str, hora_fin: str) -> str:
    url = f"{BASE_URL}/detalle-agenda-mant/{id_mantencion}"
    estado_texto = {
        'confirmado': '✅ Mantención confirmada',
        'cancelado': '❌ Mantención cancelada',
        'reprogramado': '🔄 Mantención reprogramada',
    }.get(nuevo_estado, nuevo_estado.capitalize())
    contenido = f"""
    <p style="color:#9ca3af; font-size:13px; margin:0 0 8px;">AGENDA DE MANTENCIONES</p>
    <h2 style="color:#ffffff; margin:0 0 24px; font-size:18px;">{estado_texto}</h2>
    <p style="color:#d1d5db; font-size:14px;">{titulo}</p>
    <table cellpadding="0" cellspacing="0" style="width:100%;">
      <tr>
        <td style="color:#9ca3af; font-size:13px; padding:6px 0; width:140px;">Fecha</td>
        <td style="color:#ffffff; font-size:13px; padding:6px 0;">{fecha}</td>
      </tr>
      <tr>
        <td style="color:#9ca3af; font-size:13px; padding:6px 0;">Horario</td>
        <td style="color:#ffffff; font-size:13px; padding:6px 0;">{hora_inicio} — {hora_fin}</td>
      </tr>
    </table>
    {_boton('Ver mantención', url)}
    """
    return _base_template(contenido)

def template_mencion(id_ticket: int, titulo: str, comentario: str, autor: str) -> str:
    url = f"{BASE_URL}/detalle-ticket/{id_ticket}"
    contenido = f"""
    <p style="color:#9ca3af; font-size:13px; margin:0 0 8px;">TE MENCIONARON</p>
    <h2 style="color:#ffffff; margin:0 0 24px; font-size:18px;">#{id_ticket} — {titulo}</h2>
    <div style="background:#2a2a2a; border-radius:8px; padding:16px; margin:16px 0;">
      <p style="color:#9ca3af; font-size:12px; margin:0 0 8px;">{autor}</p>
      <p style="color:#d1d5db; font-size:14px; margin:0;">{comentario}</p>
    </div>
    {_boton('Ver ticket', url)}
    """
    return _base_template(contenido)