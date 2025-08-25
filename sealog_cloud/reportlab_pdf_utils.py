"""
Enhanced PDF generation utilities using ReportLab for maritime applications
Provides professional PDF layouts for watch schedules, logbooks, and reports
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import io

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm, cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Frame, PageTemplate
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.pdfgen import canvas
    from reportlab.graphics.shapes import Drawing, Rect, Line
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics import renderPDF
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class MaritimePDFGenerator:
    """Professional PDF generator for maritime documents using ReportLab"""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required. Install with: pip install reportlab")
        
        self.doc = None
        self.story = []
        self.styles = getSampleStyleSheet()
        
        # Maritime color scheme - define colors first
        self.colors = {
            'maritime_blue': colors.Color(0.12, 0.23, 0.54),  # #1e3a8a
            'maritime_light_blue': colors.Color(0.89, 0.95, 0.99),  # #e3f2fd
            'sea_green': colors.Color(0.16, 0.66, 0.50),  # #29a745
            'warning_orange': colors.Color(1.0, 0.6, 0.0),  # #ff9900
            'header_gray': colors.Color(0.2, 0.2, 0.2),  # #333333
            'light_gray': colors.Color(0.97, 0.97, 0.97),  # #f8f9fa
        }
        
        # Setup custom styles after colors are defined
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for maritime documents"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='MaritimeTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=self.colors['maritime_blue'],
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='MaritimeSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.colors['header_gray'],
            spaceAfter=15,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=self.colors['maritime_blue'],
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        # Info box style
        self.styles.add(ParagraphStyle(
            name='InfoBox',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.colors['header_gray'],
            spaceBefore=5,
            spaceAfter=5,
            fontName='Helvetica'
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

    def create_watch_schedule_pdf(self, schedule_data: Dict, assignments_df: pd.DataFrame) -> bytes:
        """Create a professional watch schedule PDF"""
        buffer = io.BytesIO()
        
        # Create document
        self.doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=f"Watch Schedule - {schedule_data['schedule_name']}"
        )
        
        self.story = []
        
        # Header section
        self._add_header_section(schedule_data)
        
        # Schedule information
        self._add_schedule_info_section(schedule_data)
        
        # Watch assignments table
        self._add_watch_assignments_table(assignments_df, schedule_data)
        
        # Statistics and summary
        self._add_statistics_section(assignments_df)
        
        # Crew workload distribution
        self._add_crew_workload_section(assignments_df)
        
        # Signature section
        self._add_signature_section(['Master', 'Chief Officer', 'Watch Officer'])
        
        # Footer
        self._add_footer()
        
        # Build PDF
        self.doc.build(self.story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        buffer.seek(0)
        return buffer.read()
    
    def _add_header_section(self, schedule_data: Dict):
        """Add document header with maritime branding"""
        # Main title
        title = Paragraph(" WATCH SCHEDULE", self.styles['MaritimeTitle'])
        self.story.append(title)
        
        # Subtitle
        subtitle = Paragraph(schedule_data['schedule_name'], self.styles['MaritimeSubtitle'])
        self.story.append(subtitle)
        
        # Add maritime line separator
        self.story.append(Spacer(1, 10))
        
        # Create a drawing for the line
        line_drawing = Drawing(400, 10)
        line_drawing.add(Line(0, 5, 400, 5, strokeColor=self.colors['maritime_blue'], strokeWidth=2))
        self.story.append(line_drawing)
        
        self.story.append(Spacer(1, 20))
    
    def _add_schedule_info_section(self, schedule_data: Dict):
        """Add schedule information in a professional table format"""
        # Section header
        header = Paragraph("Schedule Information", self.styles['SectionHeader'])
        self.story.append(header)
        
        # Prepare info data
        info_data = [
            ['Crew Members:', f"{schedule_data['crew_count']} persons"],
            ['Watch Period:', f"{schedule_data['watch_period_hours']} hours"],
            ['Voyage Duration:', f"{schedule_data['voyage_days']} days"],
            ['Watch Type:', schedule_data['watch_type']],
            ['Start Date:', pd.to_datetime(schedule_data['start_datetime']).strftime('%Y-%m-%d %H:%M')],
            ['Created:', pd.to_datetime(schedule_data['created_date']).strftime('%Y-%m-%d')]
        ]
        
        # Create info table
        info_table = Table(info_data, colWidths=[4*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.colors['light_gray']),
            ('TEXTCOLOR', (0, 0), (0, -1), self.colors['maritime_blue']),
            ('TEXTCOLOR', (1, 0), (1, -1), self.colors['header_gray']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        self.story.append(info_table)
        self.story.append(Spacer(1, 20))
    
    def _add_watch_assignments_table(self, assignments_df: pd.DataFrame, schedule_data: Dict):
        """Add the main watch assignments table with color coding"""
        # Section header
        header = Paragraph("Watch Assignments", self.styles['SectionHeader'])
        self.story.append(header)
        
        # Prepare table data
        table_data = []
        
        # Headers
        headers = ['Date', 'Crew Member', 'Start Time', 'End Time']
        if schedule_data['watch_type'] == 'Dual Watches':
            headers.append('Partner')
        table_data.append(headers)
        
        # Format data
        formatted_df = assignments_df.copy()
        start_times = pd.to_datetime(formatted_df['watch_start'])
        end_times = pd.to_datetime(formatted_df['watch_end'])
        
        # Add data rows
        for _, row in formatted_df.iterrows():
            start_dt = pd.to_datetime(row['watch_start'])
            end_dt = pd.to_datetime(row['watch_end'])
            
            row_data = [
                start_dt.strftime('%Y-%m-%d'),
                row['crew_name'],
                start_dt.strftime('%H:%M'),
                end_dt.strftime('%H:%M')
            ]
            
            if schedule_data['watch_type'] == 'Dual Watches':
                partner = row['partner_name'] if pd.notna(row['partner_name']) else ''
                row_data.append(partner)
            
            table_data.append(row_data)
        
        # Create table
        col_widths = [3*cm, 4*cm, 2.5*cm, 2.5*cm]
        if schedule_data['watch_type'] == 'Dual Watches':
            col_widths.append(3*cm)
        
        watch_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Apply styling with crew color coding
        table_style = [
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['maritime_blue']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), self._get_crew_row_colors(formatted_df)),
        ]
        
        watch_table.setStyle(TableStyle(table_style))
        self.story.append(watch_table)
        self.story.append(Spacer(1, 20))
    
    def _get_crew_row_colors(self, df: pd.DataFrame) -> List[colors.Color]:
        """Generate alternating colors for each crew member"""
        crew_colors_list = [
            colors.Color(0.89, 0.95, 0.99),  # Light blue
            colors.Color(0.91, 0.96, 0.91),  # Light green
            colors.Color(1.0, 0.95, 0.88),   # Light orange
            colors.Color(0.95, 0.90, 0.96),  # Light purple
            colors.Color(0.88, 0.95, 0.94),  # Light teal
            colors.Color(1.0, 0.97, 0.88),   # Light yellow
            colors.Color(0.99, 0.89, 0.93),  # Light pink
            colors.Color(0.95, 0.97, 0.91),  # Light lime
        ]
        
        unique_crew = df['crew_name'].unique()
        crew_color_map = {crew: crew_colors_list[i % len(crew_colors_list)] 
                         for i, crew in enumerate(unique_crew)}
        
        return [crew_color_map[row['crew_name']] for _, row in df.iterrows()]
    
    def _add_statistics_section(self, assignments_df: pd.DataFrame):
        """Add statistics section with charts"""
        # Section header
        header = Paragraph("Schedule Statistics", self.styles['SectionHeader'])
        self.story.append(header)
        
        # Calculate statistics
        start_times = pd.to_datetime(assignments_df['watch_start'])
        end_times = pd.to_datetime(assignments_df['watch_end'])
        durations = (end_times - start_times).dt.total_seconds() / 3600
        
        stats_data = [
            ['Total Watches:', str(len(assignments_df))],
            ['Average Duration:', f"{durations.mean():.1f} hours"],
            ['Active Crew:', str(assignments_df['crew_name'].nunique())],
            ['Total Watch Hours:', f"{durations.sum():.1f} hours"],
            ['Schedule Span:', f"{(end_times.max() - start_times.min()).days} days"]
        ]
        
        # Create statistics table
        stats_table = Table(stats_data, colWidths=[4*cm, 4*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.colors['maritime_light_blue']),
            ('TEXTCOLOR', (0, 0), (0, -1), self.colors['maritime_blue']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        self.story.append(stats_table)
        self.story.append(Spacer(1, 20))
    
    def _add_crew_workload_section(self, assignments_df: pd.DataFrame):
        """Add crew workload distribution table"""
        # Section header
        header = Paragraph("Crew Workload Distribution", self.styles['SectionHeader'])
        self.story.append(header)
        
        # Calculate workload per crew member
        crew_stats = []
        for crew_name in assignments_df['crew_name'].unique():
            crew_data = assignments_df[assignments_df['crew_name'] == crew_name]
            
            start_times = pd.to_datetime(crew_data['watch_start'])
            end_times = pd.to_datetime(crew_data['watch_end'])
            total_hours = ((end_times - start_times).dt.total_seconds() / 3600).sum()
            
            crew_stats.append([
                crew_name,
                str(len(crew_data)),
                f"{total_hours:.1f}h",
                f"{total_hours / len(crew_data):.1f}h"
            ])
        
        # Sort by crew name
        crew_stats.sort(key=lambda x: x[0])
        
        # Add headers
        workload_data = [['Crew Member', 'Watches', 'Total Hours', 'Avg per Watch']]
        workload_data.extend(crew_stats)
        
        # Create workload table
        workload_table = Table(workload_data, colWidths=[4*cm, 2*cm, 2.5*cm, 2.5*cm])
        workload_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['sea_green']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            # Data
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.colors['header_gray']),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            # General
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors['light_gray']] * 10),
        ]))
        
        self.story.append(workload_table)
        self.story.append(Spacer(1, 30))
    
    def _add_signature_section(self, signature_labels: List[str]):
        """Add signature section for official approval"""
        # Section header
        header = Paragraph("Official Approval", self.styles['SectionHeader'])
        self.story.append(header)
        
        # Create signature table
        signature_data = []
        signature_row = []
        
        for label in signature_labels:
            signature_row.append(f"_" * 25 + f"\n{label}")
        
        signature_data.append(signature_row)
        
        # Date row
        date_row = ["_" * 25 + "\nDate"] * len(signature_labels)
        signature_data.append(date_row)
        
        sig_table = Table(signature_data, colWidths=[4*cm] * len(signature_labels))
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        self.story.append(sig_table)
    
    def _add_footer(self):
        """Add document footer"""
        self.story.append(Spacer(1, 30))
        
        footer_text = f"Generated by Seamans Book Cloud - Watch Scheduler<br/>Created on {datetime.now().strftime('%Y-%m-%d at %H:%M')}"
        footer = Paragraph(footer_text, self.styles['Footer'])
        self.story.append(footer)
    
    def _add_page_number(self, canvas, doc):
        """Add page numbers to each page"""
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.gray)
        
        # Page number
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(A4[0] - 2*cm, 1*cm, text)
        
        # Document title in header
        canvas.drawString(2*cm, A4[1] - 1*cm, "Watch Schedule - Seamans Book Cloud")
        
        canvas.restoreState()

    def create_crew_logbook_pdf(self, entries_df: pd.DataFrame, user_name: str = "") -> bytes:
        """Create a professional crew logbook PDF"""
        buffer = io.BytesIO()
        
        self.doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=f"Crew Logbook - {user_name}"
        )
        
        self.story = []
        
        # Header
        title = Paragraph(" CREW LOGBOOK", self.styles['MaritimeTitle'])
        self.story.append(title)
        
        if user_name:
            subtitle = Paragraph(f"Seaman's Record - {user_name}", self.styles['MaritimeSubtitle'])
            self.story.append(subtitle)
        
        self.story.append(Spacer(1, 30))
        
        # Logbook entries table
        if not entries_df.empty:
            self._add_logbook_entries_table(entries_df)
            self._add_logbook_summary(entries_df)
        
        # Signature section
        self._add_signature_section(['Master', 'Seaman'])
        self._add_footer()
        
        # Build PDF
        self.doc.build(self.story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        buffer.seek(0)
        return buffer.read()
    
    def _add_logbook_entries_table(self, entries_df: pd.DataFrame):
        """Add logbook entries in a professional table"""
        # Prepare table data
        table_data = [['Ship Name', 'Joining Port', 'Joining Date', 'Leaving Port', 'Leaving Date', 'Capacity', 'Sea Days', 'Sea Miles']]
        
        for _, row in entries_df.iterrows():
            table_data.append([
                row.get('ship_name', ''),
                row.get('place_joining', ''),
                pd.to_datetime(row.get('date_joining')).strftime('%Y-%m-%d') if pd.notna(row.get('date_joining')) else '',
                row.get('place_leaving', ''),
                pd.to_datetime(row.get('date_leaving')).strftime('%Y-%m-%d') if pd.notna(row.get('date_leaving')) else '',
                row.get('capacity', ''),
                str(row.get('sea_days', 0)),
                f"{row.get('sea_miles', 0):.1f}"
            ])
        
        # Create table with appropriate column widths
        col_widths = [2.5*cm, 2.5*cm, 2*cm, 2.5*cm, 2*cm, 2*cm, 1.5*cm, 1.5*cm]
        
        logbook_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        logbook_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['maritime_blue']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors['light_gray']] * 50),
        ]))
        
        self.story.append(logbook_table)
        self.story.append(Spacer(1, 20))
    
    def _add_logbook_summary(self, entries_df: pd.DataFrame):
        """Add summary statistics for logbook"""
        total_sea_days = entries_df['sea_days'].sum() if 'sea_days' in entries_df.columns else 0
        total_sea_miles = entries_df['sea_miles'].sum() if 'sea_miles' in entries_df.columns else 0
        
        summary_data = [
            ['Total Entries:', str(len(entries_df))],
            ['Total Sea Days:', str(total_sea_days)],
            ['Total Sea Miles:', f"{total_sea_miles:.1f} nm"],
            ['Average per Entry:', f"{total_sea_miles/len(entries_df):.1f} nm" if len(entries_df) > 0 else "0 nm"]
        ]
        
        summary_table = Table(summary_data, colWidths=[4*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.colors['maritime_light_blue']),
            ('TEXTCOLOR', (0, 0), (0, -1), self.colors['maritime_blue']),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        self.story.append(summary_table)

# Streamlit integration functions
def export_watch_schedule_reportlab_pdf(schedule_data: Dict, assignments_df: pd.DataFrame):
    """Export watch schedule using ReportLab with download button"""
    if not REPORTLAB_AVAILABLE:
        st.error(" ReportLab is required for professional PDF generation. Install with: `pip install reportlab`")
        return
    
    try:
        generator = MaritimePDFGenerator()
        pdf_bytes = generator.create_watch_schedule_pdf(schedule_data, assignments_df)
        
        st.download_button(
            label=" Download Professional PDF",
            data=pdf_bytes,
            file_name=f"{schedule_data['schedule_name'].replace(' ', '_')}_watch_schedule.pdf",
            mime="application/pdf",
            help="Professional PDF with maritime styling and color-coded crew assignments"
        )
        
        st.success(" Professional PDF generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")

def export_crew_logbook_reportlab_pdf(entries_df: pd.DataFrame, user_name: str = ""):
    """Export crew logbook using ReportLab with download button"""
    if not REPORTLAB_AVAILABLE:
        st.error(" ReportLab is required for professional PDF generation. Install with: `pip install reportlab`")
        return
    
    try:
        generator = MaritimePDFGenerator()
        pdf_bytes = generator.create_crew_logbook_pdf(entries_df, user_name)
        
        st.download_button(
            label=" Download Crew Logbook PDF",
            data=pdf_bytes,
            file_name=f"crew_logbook_{user_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            help="Professional crew logbook with maritime styling"
        )
        
        st.success(" Crew logbook PDF generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating logbook PDF: {str(e)}")

def check_reportlab_installation():
    """Check if ReportLab is installed and display status"""
    if REPORTLAB_AVAILABLE:
        st.success(" ReportLab is installed - Professional PDF generation available")
        return True
    else:
        st.warning(" ReportLab not installed - Using fallback HTML export")
        st.info(" **Install ReportLab for professional PDFs:** `pip install reportlab`")
        return False

# Demo function for testing
def demo_reportlab_pdf():
    """Demo function to test ReportLab PDF generation"""
    st.subheader(" ReportLab PDF Demo")
    
    if not check_reportlab_installation():
        return
    
    # Create sample data
    sample_schedule = {
        'schedule_name': 'Demo Atlantic Crossing',
        'crew_count': 4,
        'watch_period_hours': 4.0,
        'voyage_days': 7,
        'watch_type': 'Solo Watches',
        'start_datetime': datetime.now(),
        'created_date': datetime.now()
    }
    
    sample_assignments = pd.DataFrame({
        'crew_name': ['John Smith', 'Jane Doe', 'Mike Johnson', 'Sarah Wilson'] * 5,
        'watch_start': pd.date_range(start=datetime.now(), periods=20, freq='4H'),
        'watch_end': pd.date_range(start=datetime.now() + pd.Timedelta(hours=4), periods=20, freq='4H'),
        'watch_number': range(1, 21),
        'partner_name': [None] * 20
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(" Generate Demo Watch Schedule PDF"):
            export_watch_schedule_reportlab_pdf(sample_schedule, sample_assignments)
    
    with col2:
        # Sample logbook data
        sample_logbook = pd.DataFrame({
            'ship_name': ['MV Example', 'MV Test Ship', 'MV Demo'],
            'place_joining': ['Southampton', 'Rotterdam', 'Hamburg'],
            'date_joining': ['2025-01-01', '2025-01-15', '2025-02-01'],
            'place_leaving': ['New York', 'Southampton', 'Rotterdam'],
            'date_leaving': ['2025-01-10', '2025-01-25', '2025-02-10'],
            'capacity': ['AB Seaman', 'Bosun', 'AB Seaman'],
            'sea_days': [9, 10, 9],
            'sea_miles': [3450.5, 320.1, 380.7]
        })
        
        if st.button(" Generate Demo Logbook PDF"):
            export_crew_logbook_reportlab_pdf(sample_logbook, "Demo User")

# Integration with existing watch scheduler
def integrate_reportlab_with_watch_scheduler():
    """
    Integration instructions for existing watch scheduler:
    
    1. Add this import to your watch_scheduler.py:
       from reportlab_pdf_utils import export_watch_schedule_reportlab_pdf, check_reportlab_installation
    
    2. Update your export_schedule_pdf function:
    """
    
    example_integration = '''
def export_schedule_pdf(schedule_id: int, assignments_df: pd.DataFrame):
    """Export schedule as PDF using ReportLab or HTML fallback"""
    try:
        conn = sqlite3.connect('sea_log.db')
        schedule_df = pd.read_sql_query(
            "SELECT * FROM watch_schedules WHERE id = ?",
            conn, params=(schedule_id,)
        )
        conn.close()
        
        if schedule_df.empty:
            st.error("Schedule not found")
            return
        
        schedule_data = schedule_df.iloc[0].to_dict()
        
        # Try ReportLab first
        from reportlab_pdf_utils import export_watch_schedule_reportlab_pdf, REPORTLAB_AVAILABLE
        
        if REPORTLAB_AVAILABLE:
            export_watch_schedule_reportlab_pdf(schedule_data, assignments_df)
        else:
            # Fallback to HTML export
            export_basic_html_schedule(schedule_id, assignments_df)
            
    except ImportError:
        # Fallback if reportlab utils not available
        export_basic_html_schedule(schedule_id, assignments_df)
    except Exception as e:
        st.error(f"Error exporting PDF: {str(e)}")
    '''
    
    return example_integration

# Additional utility functions for maritime documents
class MaritimeDocumentTemplates:
    """Templates for common maritime documents"""
    
    @staticmethod
    def create_risk_assessment_pdf(assessment_data: Dict) -> bytes:
        """Create a risk assessment PDF using ReportLab"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required")
        
        buffer = io.BytesIO()
        generator = MaritimePDFGenerator()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=f"Risk Assessment - {assessment_data.get('name', 'Unknown')}"
        )
        
        story = []
        
        # Title
        title = Paragraph(" RISK ASSESSMENT", generator.styles['MaritimeTitle'])
        story.append(title)
        
        # Assessment details
        if assessment_data.get('name'):
            subtitle = Paragraph(assessment_data['name'], generator.styles['MaritimeSubtitle'])
            story.append(subtitle)
        
        story.append(Spacer(1, 20))
        
        # Assessment info table
        info_data = [
            ['Assessment Date:', datetime.now().strftime('%Y-%m-%d')],
            ['Assessor:', assessment_data.get('assessor', 'N/A')],
            ['Vessel/Location:', assessment_data.get('location', 'N/A')],
            ['Review Date:', assessment_data.get('review_date', 'N/A')]
        ]
        
        info_table = Table(info_data, colWidths=[4*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), generator.colors['light_gray']),
            ('TEXTCOLOR', (0, 0), (0, -1), generator.colors['maritime_blue']),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Hazards section
        hazards_header = Paragraph("Identified Hazards and Controls", generator.styles['SectionHeader'])
        story.append(hazards_header)
        
        # Add hazards table if available
        if 'hazards' in assessment_data and assessment_data['hazards']:
            hazard_data = [['Hazard', 'Risk Level', 'Control Measures']]
            
            for hazard in assessment_data['hazards']:
                controls = '; '.join(hazard.get('control_measures', [])) if 'control_measures' in hazard else 'None specified'
                hazard_data.append([
                    hazard.get('name', 'Unnamed hazard'),
                    hazard.get('risk_level', 'Unknown'),
                    controls
                ])
            
            hazard_table = Table(hazard_data, colWidths=[4*cm, 2*cm, 8*cm])
            hazard_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), generator.colors['warning_orange']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, generator.colors['light_gray']] * 10),
            ]))
            
            story.append(hazard_table)
        
        story.append(Spacer(1, 30))
        
        # Signature section
        signature_data = [['_' * 25 + '\nAssessor Signature', '_' * 25 + '\nMaster Approval', '_' * 25 + '\nDate']]
        sig_table = Table(signature_data, colWidths=[5*cm, 5*cm, 4*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
        ]))
        
        story.append(sig_table)
        
        # Footer
        story.append(Spacer(1, 20))
        footer_text = f"Generated by Seamans Book Cloud - Risk Assessment Tool<br/>Created on {datetime.now().strftime('%Y-%m-%d at %H:%M')}"
        footer = Paragraph(footer_text, generator.styles['Footer'])
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()
    
    @staticmethod
    def create_country_log_pdf(entries_df: pd.DataFrame, user_name: str = "") -> bytes:
        """Create a country movement log PDF"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required")
        
        buffer = io.BytesIO()
        generator = MaritimePDFGenerator()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=f"Country Movement Log - {user_name}"
        )
        
        story = []
        
        # Header
        title = Paragraph(" COUNTRY MOVEMENT LOG", generator.styles['MaritimeTitle'])
        story.append(title)
        
        if user_name:
            subtitle = Paragraph(f"Immigration Record - {user_name}", generator.styles['MaritimeSubtitle'])
            story.append(subtitle)
        
        story.append(Spacer(1, 30))
        
        # Entries table
        if not entries_df.empty:
            table_data = [['Date', 'From Country', 'To Country', 'Entry Type', 'Description']]
            
            for _, row in entries_df.iterrows():
                table_data.append([
                    pd.to_datetime(row.get('entry_date')).strftime('%Y-%m-%d') if pd.notna(row.get('entry_date')) else '',
                    row.get('departure_country', ''),
                    row.get('arrival_country', ''),
                    row.get('entry_type', ''),
                    row.get('description', '')[:50] + '...' if len(str(row.get('description', ''))) > 50 else row.get('description', '')
                ])
            
            country_table = Table(table_data, colWidths=[2*cm, 3*cm, 3*cm, 2.5*cm, 5*cm])
            country_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), generator.colors['sea_green']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, generator.colors['light_gray']] * 50),
            ]))
            
            story.append(country_table)
        
        story.append(Spacer(1, 30))
        
        # Signature section
        signature_data = [['_' * 25 + '\nImmigration Officer', '_' * 25 + '\nSeaman Signature', '_' * 25 + '\nDate']]
        sig_table = Table(signature_data, colWidths=[5*cm, 5*cm, 4*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
        ]))
        
        story.append(sig_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()

def create_comprehensive_risk_assessment_pdf(assessment_data: Dict, risk_items: List[Dict]) -> bytes:
    """Create a comprehensive MCA-compliant risk assessment PDF"""
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab is required")
    
    buffer = io.BytesIO()
    generator = MaritimePDFGenerator()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f"Risk Assessment - {assessment_data.get('assessment_title', 'Unknown')}"
    )
    
    story = []
    
    # Document Header
    title = Paragraph(" MARITIME RISK ASSESSMENT", generator.styles['MaritimeTitle'])
    story.append(title)
    
    # Assessment title
    if assessment_data.get('assessment_title'):
        subtitle = Paragraph(assessment_data['assessment_title'], generator.styles['MaritimeSubtitle'])
        story.append(subtitle)
    
    # Add maritime line separator
    story.append(Spacer(1, 10))
    line_drawing = Drawing(400, 10)
    line_drawing.add(Line(0, 5, 400, 5, strokeColor=generator.colors['maritime_blue'], strokeWidth=2))
    story.append(line_drawing)
    story.append(Spacer(1, 20))
    
    # Assessment Information Section
    header = Paragraph("Assessment Information", generator.styles['SectionHeader'])
    story.append(header)
    
    # Assessment details table
    assessment_info = [
        ['Assessment Title:', assessment_data.get('assessment_title', 'N/A')],
        ['Vessel Name:', assessment_data.get('vessel_name', 'N/A')],
        ['Assessment Date:', assessment_data.get('assessment_date', 'N/A')],
        ['Assessor Name:', assessment_data.get('assessor_name', 'N/A')],
        ['Assessor Position:', assessment_data.get('assessor_position', 'N/A')],
        ['Operation Location:', assessment_data.get('operation_location', 'N/A')],
        ['Operation Description:', assessment_data.get('operation_description', 'N/A')],
    ]
    
    # Add environmental conditions if present
    if assessment_data.get('weather_conditions'):
        assessment_info.append(['Weather Conditions:', assessment_data['weather_conditions']])
    if assessment_data.get('sea_state'):
        assessment_info.append(['Sea State:', assessment_data['sea_state']])
    if assessment_data.get('visibility'):
        assessment_info.append(['Visibility:', assessment_data['visibility']])
    
    # Create assessment info table
    info_table = Table(assessment_info, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), generator.colors['light_gray']),
        ('TEXTCOLOR', (0, 0), (0, -1), generator.colors['maritime_blue']),
        ('TEXTCOLOR', (1, 0), (1, -1), generator.colors['header_gray']),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Risk Summary Section
    if risk_items:
        risk_summary_header = Paragraph("Risk Assessment Summary", generator.styles['SectionHeader'])
        story.append(risk_summary_header)
        
        # Calculate risk statistics
        risk_levels = [item['risk_level']['level'] for item in risk_items]
        risk_counts = {}
        for level in risk_levels:
            risk_counts[level] = risk_counts.get(level, 0) + 1
        
        high_priority_count = sum(1 for level in risk_levels if level in ['High', 'Very High'])
        
        # Summary statistics table
        summary_data = [
            ['Total Risks Identified:', str(len(risk_items))],
            ['High Priority Risks:', str(high_priority_count)],
            ['Risk Distribution:', ', '.join([f"{count} {level}" for level, count in risk_counts.items()])]
        ]
        
        summary_table = Table(summary_data, colWidths=[4*cm, 10*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), generator.colors['maritime_light_blue']),
            ('TEXTCOLOR', (0, 0), (0, -1), generator.colors['maritime_blue']),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(summary_table)
        
        # High priority warning if needed
        if high_priority_count > 0:
            warning_para = Paragraph(
                f" WARNING: {high_priority_count} HIGH PRIORITY RISK(S) REQUIRE IMMEDIATE ATTENTION",
                ParagraphStyle(
                    'Warning',
                    parent=generator.styles['Normal'],
                    fontSize=12,
                    textColor=colors.red,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold',
                    spaceBefore=10,
                    spaceAfter=10
                )
            )
            story.append(warning_para)
        
        story.append(Spacer(1, 20))
    
    # Detailed Risk Analysis Section
    if risk_items:
        detailed_header = Paragraph("Detailed Risk Analysis", generator.styles['SectionHeader'])
        story.append(detailed_header)
        
        for idx, risk_item in enumerate(risk_items, 1):
            # Risk header with color coding
            risk_level = risk_item['risk_level']['level']
            risk_color = get_risk_color(risk_level)
            
            # Risk title
            risk_title = Paragraph(
                f"Risk #{idx}: {risk_item['hazard_category']} - {risk_level}",
                ParagraphStyle(
                    'RiskTitle',
                    parent=generator.styles['SectionHeader'],
                    fontSize=12,
                    textColor=risk_color,
                    spaceBefore=15,
                    spaceAfter=10
                )
            )
            story.append(risk_title)
            
            # Risk details table
            risk_details = [
                ['Hazard Category:', risk_item['hazard_category']],
                ['Hazard Description:', risk_item['hazard_description']],
                ['Potential Consequences:', risk_item['potential_consequences']],
                ['Existing Controls:', risk_item.get('existing_controls', 'None specified')],
                ['Likelihood Score:', f"{risk_item['likelihood_score']}/5"],
                ['Severity Score:', f"{risk_item['severity_score']}/5"],
                ['Risk Level:', risk_level],
                ['Additional Controls:', risk_item.get('additional_controls', 'None specified')],
                ['Action Required:', risk_item['risk_level']['action']]
            ]
            
            risk_table = Table(risk_details, colWidths=[4*cm, 10*cm])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (0, -1), generator.colors['header_gray']),
                ('TEXTCOLOR', (1, 0), (1, -1), generator.colors['header_gray']),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                # Highlight risk level row
                ('BACKGROUND', (0, 6), (-1, 6), risk_color),
                ('TEXTCOLOR', (0, 6), (-1, 6), colors.white),
                ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
            ]))
            
            story.append(risk_table)
            story.append(Spacer(1, 10))
    
    # Risk Matrix Reference
    story.append(PageBreak())
    matrix_header = Paragraph("Risk Assessment Matrix Reference", generator.styles['SectionHeader'])
    story.append(matrix_header)
    
    # Create risk matrix table
    matrix_data = [['Likelihood →\nSeverity ↓', '1\nVery Unlikely', '2\nUnlikely', '3\nPossible', '4\nLikely', '5\nVery Likely']]
    
    severity_labels = ['1\nNegligible', '2\nMinor', '3\nModerate', '4\nMajor', '5\nCatastrophic']
    
    for sev in range(1, 6):
        row = [severity_labels[sev-1]]
        for like in range(1, 6):
            risk_level = get_risk_level_from_scores(like, sev)
            row.append(risk_level)
        matrix_data.append(row)
    
    matrix_table = Table(matrix_data, colWidths=[2.5*cm] + [2.2*cm]*5)
    matrix_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (0, 0), generator.colors['header_gray']),
        ('BACKGROUND', (1, 0), (-1, 0), generator.colors['maritime_blue']),
        ('BACKGROUND', (0, 1), (0, -1), generator.colors['maritime_blue']),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    # Add risk level colors to matrix cells
    for sev in range(1, 6):
        for like in range(1, 6):
            risk_level = get_risk_level_from_scores(like, sev)
            risk_color = get_risk_color(risk_level)
            matrix_table.setStyle(TableStyle([
                ('BACKGROUND', (like, sev), (like, sev), risk_color),
                ('TEXTCOLOR', (like, sev), (like, sev), colors.white),
                ('FONTNAME', (like, sev), (like, sev), 'Helvetica-Bold'),
            ]))
    
    story.append(matrix_table)
    story.append(Spacer(1, 20))
    
    # Risk level definitions
    definitions_header = Paragraph("Risk Level Definitions", generator.styles['SectionHeader'])
    story.append(definitions_header)
    
    definitions_data = [
        ['Very Low/Low', 'Monitor - Acceptable risk level with existing controls'],
        ['Medium', 'Review Controls - Consider additional measures to reduce risk'],
        ['High', 'Additional Controls Required - Implement further risk reduction measures'],
        ['Very High', 'Immediate Action Required - Stop operation until risk is reduced']
    ]
    
    definitions_table = Table(definitions_data, colWidths=[3*cm, 11*cm])
    definitions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), generator.colors['light_gray']),
        ('TEXTCOLOR', (0, 0), (0, -1), generator.colors['maritime_blue']),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    
    story.append(definitions_table)
    story.append(Spacer(1, 30))
    
    # Signature Section
    signature_header = Paragraph("Assessment Approval", generator.styles['SectionHeader'])
    story.append(signature_header)
    
    signature_data = [
        ['_' * 30 + '\nAssessor Signature & Date', '_' * 30 + '\nMaster/Senior Officer Approval & Date'],
        [f"\n{assessment_data.get('assessor_name', '')} - {assessment_data.get('assessor_position', '')}", '\nMaster/Senior Officer']
    ]
    
    sig_table = Table(signature_data, colWidths=[7*cm, 7*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 0), (-1, -1), 30),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(sig_table)
    story.append(Spacer(1, 20))
    
    # Footer
    footer_text = f"Generated by Seamans Book Cloud - Risk Assessment Tool<br/>MCA Compliant Maritime Risk Assessment<br/>Created on {datetime.now().strftime('%Y-%m-%d at %H:%M UTC')}"
    footer = Paragraph(footer_text, generator.styles['Footer'])
    story.append(footer)
    
    # Build PDF
    doc.build(story, onFirstPage=generator._add_page_number, onLaterPages=generator._add_page_number)
    buffer.seek(0)
    return buffer.read()

def get_risk_color(risk_level: str) -> colors.Color:
    """Get color for risk level"""
    risk_colors = {
        'Very Low': colors.Color(0.16, 0.66, 0.50),  # Green
        'Low': colors.Color(0.16, 0.66, 0.50),       # Green
        'Medium': colors.Color(1.0, 0.76, 0.03),     # Yellow
        'High': colors.Color(0.99, 0.49, 0.09),      # Orange
        'Very High': colors.Color(0.86, 0.20, 0.27)  # Red
    }
    return risk_colors.get(risk_level, colors.gray)

def get_risk_level_from_scores(likelihood: int, severity: int) -> str:
    """Get risk level from likelihood and severity scores"""
    # This should match your RISK_MATRIX from the risk assessment tool
    risk_matrix = {
        (1,1): "Very Low", (1,2): "Low", (1,3): "Medium", (1,4): "High", (1,5): "Very High",
        (2,1): "Low", (2,2): "Low", (2,3): "Medium", (2,4): "High", (2,5): "Very High",
        (3,1): "Medium", (3,2): "Medium", (3,3): "Medium", (3,4): "High", (3,5): "Very High",
        (4,1): "High", (4,2): "High", (4,3): "High", (4,4): "High", (4,5): "Very High",
        (5,1): "Very High", (5,2): "Very High", (5,3): "Very High", (5,4): "Very High", (5,5): "Very High",
    }
    return risk_matrix.get((likelihood, severity), "Unknown")

# Streamlit integration function
def export_risk_assessment_professional_pdf(assessment_data: Dict, risk_items: List[Dict]):
    """Export risk assessment using ReportLab with download button"""
    if not REPORTLAB_AVAILABLE:
        st.error(" ReportLab is required for professional PDF generation. Install with: `pip install reportlab`")
        return
    
    try:
        pdf_bytes = create_comprehensive_risk_assessment_pdf(assessment_data, risk_items)
        
        # Create filename
        title = assessment_data.get('assessment_title', 'risk_assessment')
        vessel = assessment_data.get('vessel_name', 'unknown_vessel')
        date = assessment_data.get('assessment_date', datetime.now().strftime('%Y-%m-%d'))
        filename = f"{title}_{vessel}_{date}".replace(' ', '_').replace('/', '_')
        
        st.download_button(
            label=" Download Professional Risk Assessment PDF",
            data=pdf_bytes,
            file_name=f"{filename}.pdf",
            mime="application/pdf",
            help="MCA-compliant professional risk assessment with maritime styling, risk matrix, and detailed analysis"
        )
        
        st.success(" Professional risk assessment PDF generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating risk assessment PDF: {str(e)}")

# Function to integrate with your existing risk assessment tool
def integrate_with_risk_assessment_tool():
    """
    Integration instructions for your risk assessment tool:
    
    1. Add this import to your risk_assessment.py:
       from reportlab_pdf_utils import export_risk_assessment_professional_pdf, REPORTLAB_AVAILABLE
    
    2. Update your assessment display function to include PDF export:
    """
    
    example_integration = '''
    # In your render_assessment_list() function, replace the disabled PDF button with:
    
    if st.button(f" Export PDF", key=f"export_{assessment_id}"):
        # Get assessment data
        assessment_data = {
            'assessment_title': assessment_title,
            'vessel_name': vessel_name,
            'assessment_date': assessment_date,
            'assessor_name': assessor_name,
            'assessor_position': assessor_position,
            'operation_location': operation_location,
            'operation_description': operation_description,
            'weather_conditions': weather_conditions,
            'sea_state': sea_state,
            'visibility': visibility
        }
        
        # Get risk items from database
        risk_items_data = get_assessment_risks(assessment_id)
        
        # Format risk items for PDF
        formatted_risks = []
        for risk_item in risk_items_data:
            formatted_risks.append({
                'hazard_category': risk_item[2],
                'hazard_description': risk_item[3],
                'potential_consequences': risk_item[4],
                'existing_controls': risk_item[5],
                'likelihood_score': risk_item[6],
                'severity_score': risk_item[7],
                'additional_controls': risk_item[8],
                'risk_level': {
                    'level': risk_item[8],
                    'action': risk_item[9]
                }
            })
        
        # Export PDF
        export_risk_assessment_professional_pdf(assessment_data, formatted_risks)
    '''
    
    return example_integration
    
# Export functions for Streamlit integration
def export_risk_assessment_reportlab_pdf(assessment_data: Dict):
    """Export risk assessment using ReportLab with download button"""
    if not REPORTLAB_AVAILABLE:
        st.error(" ReportLab is required for professional PDF generation.")
        return
    
    try:
        pdf_bytes = MaritimeDocumentTemplates.create_risk_assessment_pdf(assessment_data)
        
        st.download_button(
            label=" Download Risk Assessment PDF",
            data=pdf_bytes,
            file_name=f"risk_assessment_{assessment_data.get('name', 'unknown').replace(' ', '_')}.pdf",
            mime="application/pdf",
            help="Professional risk assessment with maritime styling"
        )
        
        st.success(" Risk assessment PDF generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating risk assessment PDF: {str(e)}")

def export_country_log_reportlab_pdf(entries_df: pd.DataFrame, user_name: str = ""):
    """Export country log using ReportLab with download button"""
    if not REPORTLAB_AVAILABLE:
        st.error(" ReportLab is required for professional PDF generation.")
        return
    
    try:
        pdf_bytes = MaritimeDocumentTemplates.create_country_log_pdf(entries_df, user_name)
        
        st.download_button(
            label=" Download Country Log PDF",
            data=pdf_bytes,
            file_name=f"country_log_{user_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            help="Professional country movement log with maritime styling"
        )
        
        st.success(" Country log PDF generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating country log PDF: {str(e)}")

# Installation and setup instructions
def show_reportlab_setup_instructions():
    """Display setup instructions for ReportLab"""
    st.markdown("""
    ##  ReportLab Setup Instructions
    
    ### Installation
    ```bash
    pip install reportlab
    ```
    
    ### Features
     **Professional PDF layouts** with maritime branding  
     **Color-coded crew assignments** matching your display tables  
     **Custom maritime styling** with nautical themes  
     **Proper table formatting** with headers and statistics  
     **Signature sections** for official documentation  
     **Page numbering** and headers/footers  
     **Multiple document types** (watch schedules, logbooks, risk assessments)  
    
    ### Usage
    Once installed, your export buttons will automatically use ReportLab for professional PDFs instead of HTML fallback.
    
    ### File Structure
    ```
    your_app/
     core/
        reportlab_pdf_utils.py  # This file
     tools/
         watch_scheduler.py      # Updated to use ReportLab
    ```
    """)

# Version info and requirements
REPORTLAB_VERSION_INFO = {
    'required_version': '4.0.0',
    'features': [
        'Professional table layouts with maritime styling',
        'Color-coded crew assignments matching display tables',
        'Custom maritime branding and themes',
        'Signature sections for official approval',
        'Multi-page support with headers and footers',
        'Statistics and summary sections',
        'Cross-platform PDF compatibility'
    ],
    'document_types': [
        'Watch Schedules',
        'Crew Logbooks', 
        'Country Movement Logs',
        'Risk Assessments',
        'Ship Logs',
        'Custom Maritime Reports'
    ]
}