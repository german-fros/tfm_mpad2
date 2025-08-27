import streamlit as st
import pandas as pd
import base64
import io
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from config.logger_config import LoggerSetup, log_function

# LOGGER SETUP
logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)


@log_function("export_position_tab_to_pdf")
def export_position_tab_to_pdf(position: str, player1_name: str, player1_team: str, 
                                player2_name: str, player2_team: str, 
                                visualizations: Dict[str, plt.Figure]) -> bytes:
    """
    Exportar contenido de un tab de posición específica a PDF.
    
    Args:
        position: Nombre de la posición (ej. "Goalkeeper", "Defender", etc.).
        player1_name: Nombre del primer jugador.
        player1_team: Equipo del primer jugador.
        player2_name: Nombre del segundo jugador.
        player2_team: Equipo del segundo jugador.
        visualizations: Diccionario con las figuras de matplotlib a incluir.
    
    Returns:
        Contenido del PDF en bytes.
    """
    try:
        # Crear buffer para el PDF
        buffer = io.BytesIO()
        
        # Configurar documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        
        # Crear estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.black,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.gray,
            spaceAfter=8,
            alignment=TA_CENTER
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=6
        )
        
        # Contenido del PDF
        content = []
        
        # Header
        position_display = {
            'Goalkeeper': 'Portero',
            'Defender': 'Defensore', 
            'Midfielder': 'Centrocampista',
            'Forward': 'Delantero'
        }.get(position, position)
        
        content.append(Paragraph(f"Comparación de {position_display}s", title_style))
        content.append(Paragraph(f"MLS 2024 - Análisis de Jugadores", subtitle_style))
        content.append(Spacer(1, 12))
        
        # Información de los jugadores
        player_info_data = [
            ['Jugador 1', 'Jugador 2'],
            [f"{player1_name}", f"{player2_name}"],
            [f"Equipo: {player1_team}", f"Equipo: {player2_team}"],
            [f"Posición: {position_display}", f"Posición: {position_display}"]
        ]
        
        player_table = Table(player_info_data, colWidths=[3*inch, 3*inch])
        player_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
            ('BACKGROUND', (0, 1), (0, 1), colors.Color(190/255, 50/255, 43/255)),  # Player 1 name cell - #BE322B
            ('BACKGROUND', (1, 1), (1, 1), colors.Color(26/255, 120/255, 207/255)),  # Player 2 name cell - #1A78CF
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray)
        ]))
        
        content.append(player_table)
        content.append(Spacer(1, 20))
        
        # Agregar visualizaciones
        for viz_name, fig in visualizations.items():
            if fig is not None:
                # Guardar figura en buffer
                img_buffer = io.BytesIO()
                fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                img_buffer.seek(0)
                
                # Crear imagen para el PDF
                img = Image(img_buffer, width=6*inch, height=4*inch)
                content.append(Paragraph(f"{viz_name}", subtitle_style))
                content.append(img)
                content.append(Spacer(1, 12))
                
                plt.close(fig)  # Liberar memoria
        
        # Footer
        content.append(Spacer(1, 20))
        footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} | MLS Player Comparison Dashboard"
        content.append(Paragraph(footer_text, normal_style))
        
        # Generar PDF
        doc.build(content)
        buffer.seek(0)
        
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Error generando PDF para {position}: {str(e)}")
        raise Exception(f"Error generando PDF: {str(e)}")


@log_function("create_pdf_download_button")
def create_pdf_download_button(position: str, player1_name: str, player1_team: str,
                               player2_name: str, player2_team: str, 
                               visualizations: Dict[str, plt.Figure]) -> None:
    """
    Crear botón de descarga de PDF para comparación de jugadores.
    
    Args:
        position: Nombre de la posición.
        player1_name: Nombre del primer jugador.
        player1_team: Equipo del primer jugador.
        player2_name: Nombre del segundo jugador.
        player2_team: Equipo del segundo jugador.
        visualizations: Diccionario con las figuras a incluir.
    """
    try:
        # Generar nombre de archivo
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"Comparison_{position}_{player1_name}-vs-{player2_name}_{date_str}.pdf"
        
        # Generar PDF
        pdf_data = export_position_tab_to_pdf(
            position, player1_name, player1_team, 
            player2_name, player2_team, visualizations
        )
        
        # Crear botón de descarga
        st.download_button(
            label="📄 Descargar Comparación PDF",
            data=pdf_data,
            file_name=filename,
            mime="application/pdf",
            help=f"Descargar comparación completa de {position.lower()}s en formato PDF",
            use_container_width=True
        )
        
    except Exception as e:
        logger.error(f"Error creando botón de descarga PDF: {str(e)}")
        st.error(f"Error preparando descarga PDF: {str(e)}")