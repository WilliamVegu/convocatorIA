"""Executive One-Pager candidate presentation builder with official TCS branding."""
from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime


class OnePagerBuilder:
    """Builds a pixel-perfect, printable HTML executive summary for presenting candidates to clients (e.g. BCP)."""

    @staticmethod
    def build_html(
        candidato_nombre: str,
        dni_masked: str,
        perfil_puesto: str,
        cliente: str,
        anios_experiencia: float | str,
        distrito: str,
        modalidad: str,
        skills: List[str],
        resumen_tecnico: str,
        disponibilidad: str,
        expectativa_salarial: float,
        bgc_status: str,
        evaluador_nombre: str,
        dictamen_humano: str,
        alumni_tcs: bool = False,
        fit_score: float = 85.0,
    ) -> str:
        """Render self-contained styled HTML One-Pager."""
        now_str = datetime.now().strftime("%d/%m/%Y")
        skills_chips = "".join([f'<span class="skill-chip">{s}</span>' for s in skills[:12]])

        alumni_badge = (
            '<span style="background: #9B59B6; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-left: 8px;">'
            '🟣 TALENTO BOOMERANG TCS</span>'
            if alumni_tcs else ""
        )

        bgc_badge = (
            '<span style="color: #2ECC71; font-weight: bold;">✔ Aprobado (Sin antecedentes)</span>'
            if "Aprobado" in bgc_status else f'<span style="color: #E74C3C; font-weight: bold;">{bgc_status}</span>'
        )

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1E293B;
    background: #FFFFFF;
    margin: 0;
    padding: 24px;
  }}
  .card {{
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    max-width: 800px;
    margin: 0 auto;
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #0076CE;
    padding-bottom: 12px;
    margin-bottom: 18px;
  }}
  .brand-title {{
    color: #0A192F;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 0.5px;
  }}
  .brand-sub {{
    color: #0076CE;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
  }}
  .client-tag {{
    background: #0A192F;
    color: #00B4D8;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 700;
  }}
  .candidate-title {{
    font-size: 22px;
    font-weight: 700;
    color: #0F172A;
    margin: 0 0 4px 0;
  }}
  .role-subtitle {{
    font-size: 15px;
    color: #475569;
    margin-bottom: 16px;
  }}
  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 18px;
  }}
  .info-box {{
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px 14px;
  }}
  .info-label {{
    font-size: 11px;
    color: #64748B;
    text-transform: uppercase;
    font-weight: 700;
    margin-bottom: 4px;
  }}
  .info-val {{
    font-size: 13px;
    color: #0F172A;
    font-weight: 600;
  }}
  .skill-chip {{
    display: inline-block;
    background: #E0F2FE;
    color: #0369A1;
    border: 1px solid #BAE6FD;
    padding: 4px 10px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 600;
    margin: 3px;
  }}
  .score-badge {{
    background: #DCFCE7;
    color: #166534;
    border: 1px solid #86EFAC;
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 800;
    display: inline-block;
  }}
  .section-title {{
    font-size: 13px;
    font-weight: 700;
    color: #0A192F;
    text-transform: uppercase;
    border-left: 3px solid #0076CE;
    padding-left: 8px;
    margin: 16px 0 8px 0;
  }}
  .footer {{
    margin-top: 20px;
    padding-top: 10px;
    border-top: 1px solid #E2E8F0;
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #94A3B8;
  }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <div>
      <div class="brand-title">TATA CONSULTANCY SERVICES</div>
      <div class="brand-sub">Talent Acquisition & Technical Delivery — Perú</div>
    </div>
    <div class="client-tag">TERNA: {cliente.upper()}</div>
  </div>

  <div class="candidate-title">{candidato_nombre} {alumni_badge}</div>
  <div class="role-subtitle">Postulación: <b>{perfil_puesto}</b> &nbsp;|&nbsp; DNI: <code>{dni_masked}</code></div>

  <div class="grid-2">
    <div class="info-box">
      <div class="info-label">Compatibilidad Técnica (Fit Score)</div>
      <div class="score-badge">🎯 {fit_score:.0f}% Match Requerimiento</div>
    </div>
    <div class="info-box">
      <div class="info-label">Experiencia y Residencia</div>
      <div class="info-val">{anios_experiencia} años &nbsp;|&nbsp; {distrito} ({modalidad})</div>
    </div>
  </div>

  <div class="section-title">Resumen Profesional y Fortalezas Clave</div>
  <div class="info-box" style="font-size: 13px; line-height: 1.5; color: #334155;">
    {resumen_tecnico or 'Perfil con trayectoria técnica sólida en desarrollo de soluciones corporativas.'}
  </div>

  <div class="section-title">Competencias Técnicas Principales</div>
  <div style="margin-bottom: 12px;">
    {skills_chips if skills_chips else '<span style="font-size: 12px; color: #64748B;">Habilidades en evaluación</span>'}
  </div>

  <div class="grid-2">
    <div class="info-box">
      <div class="info-label">Disponibilidad de Inicio</div>
      <div class="info-val">{disponibilidad}</div>
    </div>
    <div class="info-box">
      <div class="info-label">Pretensión Salarial Mensual</div>
      <div class="info-val">S/. {expectativa_salarial:,.2f} Bruto (Negociable)</div>
    </div>
  </div>

  <div class="grid-2">
    <div class="info-box">
      <div class="info-label">Filtros de Seguridad & Compliance</div>
      <div class="info-val">{bgc_badge}</div>
    </div>
    <div class="info-box">
      <div class="info-label">Dictamen Reclutamiento TCS</div>
      <div class="info-val" style="color: #0A192F;">✔ {dictamen_humano.replace('_', ' ')}</div>
    </div>
  </div>

  <div class="footer">
    <div>Evaluador Responsable: <b>{evaluador_nombre}</b> (TCS Talent Acquisition)</div>
    <div>Fecha de Emisión: {now_str} &nbsp;|&nbsp; TCS Confidential</div>
  </div>
</div>
</body>
</html>"""
        return html
