import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any

class PDFExporter:
    """Reusable PDF export utility for maritime applications"""
    
    def __init__(self):
        self.default_styles = self._get_default_styles()
    
    def _get_default_styles(self) -> str:
        """Get default CSS styles for PDF exports"""
        return """
        @media print {
            body { margin: 0; }
            .no-print { display: none; }
        }
        
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.4;
            color: #333;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #1e3a8a;
            padding-bottom: 20px;
        }
        
        .header h1 {
            color: #1e3a8a;
            margin: 0;
            font-size: 28px;
        }
        
        .header h2 {
            color: #666;
            margin: 10px 0 0 0;
            font-weight: normal;
            font-size: 18px;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        
        .info-item {
            padding: 10px;
            background-color: white;
            border-radius: 5px;
            border-left: 4px solid #1e3a8a;
        }
        
        .info-label {
            font-weight: bold;
            color: #1e3a8a;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .info-value {
            font-size: 16px;
            color: #333;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .data-table thead tr {
            background-color: #1e3a8a;
            color: white;
        }
        
        .data-table th {
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            border-right: 1px solid rgba(255,255,255,0.2);
        }
        
        .data-table td {
            padding: 12px;
            border-right: 1px solid rgba(0,0,0,0.1);
            border-bottom: 1px solid #ddd;
        }
        
        .statistics {
            margin-top: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        
        .stat-card {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #1e3a8a;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #1e3a8a;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
        
        .signature-section {
            margin-top: 40px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 30px;
        }
        
        .signature-box {
            border-top: 2px solid #333;
            padding-top: 10px;
            text-align: center;
        }
        
        .signature-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }
        
        .page-break {
            page-break-before: always;
        }
        """
    
    def export_dataframe_to_html_pdf(self, 
                                   df: pd.DataFrame,
                                   title: str,
                                   subtitle: str = "",
                                   info_data: Dict[str, Any] = None,
                                   statistics: Dict[str, Any] = None,
                                   filename: str = None,
                                   custom_styles: str = "",
                                   row_colors: Dict[str, str] = None,
                                   signatures: List[str] = None) -> str:
        """
        Export a DataFrame to HTML format suitable for PDF printing
        
        Args:
            df: DataFrame to export
            title: Main title for the document
            subtitle: Subtitle for the document
            info_data: Dictionary of key-value pairs for info section
            statistics: Dictionary of statistics to display
            filename: Filename for download (auto-generated if None)
            custom_styles: Additional CSS styles
            row_colors: Dictionary mapping row identifiers to colors
            signatures: List of signature labels to add at bottom
        
        Returns:
            HTML content as string
        """
        if filename is None:
            filename = f"{title.replace(' ', '_')}.html"
        
        # Build HTML content
        html_content = self._build_html_document(
            df, title, subtitle, info_data, statistics, 
            custom_styles, row_colors, signatures
        )
        
        # Create download button
        st.download_button(
            label=" Download PDF (HTML)",
            data=html_content.encode('utf-8'),
            file_name=filename,
            mime="text/html",
            help="Download as HTML file - open in browser and print to PDF for best results"
        )
        
        return html_content
    
    def _build_html_document(self,
                           df: pd.DataFrame,
                           title: str,
                           subtitle: str,
                           info_data: Dict[str, Any],
                           statistics: Dict[str, Any],
                           custom_styles: str,
                           row_colors: Dict[str, str],
                           signatures: List[str]) -> str:
        """Build the complete HTML document"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                {self.default_styles}
                {custom_styles}
            </style>
        </head>
        <body>
        """
        
        # Add header
        html += self._build_header(title, subtitle)
        
        # Add info section if provided
        if info_data:
            html += self._build_info_section(info_data)
        
        # Add main data table
        html += self._build_data_table(df, row_colors)
        
        # Add statistics if provided
        if statistics:
            html += self._build_statistics_section(statistics)
        
        # Add signatures if provided
        if signatures:
            html += self._build_signature_section(signatures)
        
        # Add footer
        html += self._build_footer()
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _build_header(self, title: str, subtitle: str) -> str:
        """Build header section"""
        subtitle_html = f"<h2>{subtitle}</h2>" if subtitle else ""
        
        return f"""
        <div class="header">
            <h1> {title}</h1>
            {subtitle_html}
        </div>
        """
    
    def _build_info_section(self, info_data: Dict[str, Any]) -> str:
        """Build information grid section"""
        html = '<div class="info-grid">'
        
        for label, value in info_data.items():
            html += f"""
            <div class="info-item">
                <div class="info-label">{label}</div>
                <div class="info-value">{value}</div>
            </div>
            """
        
        html += '</div>'
        return html
    
    def _build_data_table(self, df: pd.DataFrame, row_colors: Dict[str, str] = None) -> str:
        """Build main data table"""
        html = '<table class="data-table"><thead><tr>'
        
        # Add headers
        for col in df.columns:
            html += f'<th>{col}</th>'
        
        html += '</tr></thead><tbody>'
        
        # Add data rows
        for idx, row in df.iterrows():
            # Determine row color
            row_style = ""
            if row_colors:
                # Try to find a color based on first column value or index
                key = str(row.iloc[0]) if len(row) > 0 else str(idx)
                if key in row_colors:
                    row_style = f' style="background-color: {row_colors[key]};"'
            
            html += f'<tr{row_style}>'
            
            for value in row:
                # Handle NaN values
                display_value = "" if pd.isna(value) else str(value)
                html += f'<td>{display_value}</td>'
            
            html += '</tr>'
        
        html += '</tbody></table>'
        return html
    
    def _build_statistics_section(self, statistics: Dict[str, Any]) -> str:
        """Build statistics section"""
        html = '<div class="statistics">'
        
        for label, value in statistics.items():
            html += f"""
            <div class="stat-card">
                <div class="stat-value">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            """
        
        html += '</div>'
        return html
    
    def _build_signature_section(self, signatures: List[str]) -> str:
        """Build signature section"""
        html = '<div class="signature-section">'
        
        for signature_label in signatures:
            html += f"""
            <div class="signature-box">
                <div style="height: 40px;"></div>
                <div class="signature-label">{signature_label}</div>
            </div>
            """
        
        html += '</div>'
        return html
    
    def _build_footer(self) -> str:
        """Build footer section"""
        return f"""
        <div class="footer">
            <p>Generated by Seamans Book Cloud</p>
            <p>Created on {datetime.now().strftime('%Y-%m-%d at %H:%M')}</p>
        </div>
        """

# Convenience functions for common export types

def export_crew_logbook_pdf(entries_df: pd.DataFrame, user_name: str = ""):
    """Export crew logbook entries as PDF"""
    exporter = PDFExporter()
    
    # Prepare data
    if entries_df.empty:
        st.warning("No entries to export")
        return
    
    # Format dataframe for export
    export_df = entries_df.copy()
    
    # Format dates
    if 'date_joining' in export_df.columns:
        export_df['date_joining'] = pd.to_datetime(export_df['date_joining']).dt.strftime('%Y-%m-%d')
    if 'date_leaving' in export_df.columns:
        export_df['date_leaving'] = pd.to_datetime(export_df['date_leaving']).dt.strftime('%Y-%m-%d')
    
    # Select and rename columns for display
    display_columns = {
        'ship_name': 'Ship Name',
        'place_joining': 'Port of Joining',
        'date_joining': 'Date Joining',
        'place_leaving': 'Port of Leaving',
        'date_leaving': 'Date Leaving',
        'capacity': 'Capacity',
        'entry_type': 'Entry Type',
        'sea_days': 'Sea Days',
        'sea_miles': 'Sea Miles'
    }
    
    # Filter and rename columns
    available_columns = {k: v for k, v in display_columns.items() if k in export_df.columns}
    export_df = export_df[list(available_columns.keys())].rename(columns=available_columns)
    
    # Calculate statistics
    total_sea_days = entries_df['sea_days'].sum() if 'sea_days' in entries_df.columns else 0
    total_sea_miles = entries_df['sea_miles'].sum() if 'sea_miles' in entries_df.columns else 0
    total_entries = len(entries_df)
    
    info_data = {
        'Seaman Name': user_name,
        'Total Entries': total_entries,
        'Export Date': datetime.now().strftime('%Y-%m-%d'),
        'Period': f"{entries_df['date_joining'].min()} to {entries_df['date_leaving'].max()}" if 'date_joining' in entries_df.columns else "N/A"
    }
    
    statistics = {
        'Total Sea Days': total_sea_days,
        'Total Sea Miles': f"{total_sea_miles:.1f}",
        'Average per Entry': f"{total_sea_miles/total_entries:.1f}" if total_entries > 0 else "0",
        'Entries': total_entries
    }
    
    # Row colors based on entry type
    row_colors = {}
    if 'Entry Type' in export_df.columns:
        for idx, row in export_df.iterrows():
            if row['Entry Type'] == 'Sea Going':
                row_colors[str(row.iloc[0])] = "#E3F2FD"  # Light blue
            else:
                row_colors[str(row.iloc[0])] = "#E8F5E8"  # Light green
    
    signatures = ['Master Signature', 'Seaman Signature', 'Date']
    
    return exporter.export_dataframe_to_html_pdf(
        df=export_df,
        title="Crew Logbook",
        subtitle=f"Seaman's Record - {user_name}",
        info_data=info_data,
        statistics=statistics,
        filename=f"crew_logbook_{user_name.replace(' ', '_')}.html",
        row_colors=row_colors,
        signatures=signatures
    )

def export_country_log_pdf(entries_df: pd.DataFrame, user_name: str = ""):
    """Export country log entries as PDF"""
    exporter = PDFExporter()
    
    if entries_df.empty:
        st.warning("No country entries to export")
        return
    
    # Format dataframe for export
    export_df = entries_df.copy()
    
    # Format dates
    if 'entry_date' in export_df.columns:
        export_df['entry_date'] = pd.to_datetime(export_df['entry_date']).dt.strftime('%Y-%m-%d')
    
    # Select and rename columns
    display_columns = {
        'entry_date': 'Date',
        'departure_country': 'From Country',
        'arrival_country': 'To Country',
        'entry_type': 'Entry Type',
        'description': 'Description'
    }
    
    available_columns = {k: v for k, v in display_columns.items() if k in export_df.columns}
    export_df = export_df[list(available_columns.keys())].rename(columns=available_columns)
    
    info_data = {
        'Seaman Name': user_name,
        'Total Entries': len(entries_df),
        'Export Date': datetime.now().strftime('%Y-%m-%d'),
        'Period': f"{entries_df['entry_date'].min()} to {entries_df['entry_date'].max()}" if 'entry_date' in entries_df.columns else "N/A"
    }
    
    # Count unique countries
    unique_countries = set()
    if 'departure_country' in entries_df.columns:
        unique_countries.update(entries_df['departure_country'].dropna())
    if 'arrival_country' in entries_df.columns:
        unique_countries.update(entries_df['arrival_country'].dropna())
    
    statistics = {
        'Total Movements': len(entries_df),
        'Countries Visited': len(unique_countries),
        'Sea Entries': len(entries_df[entries_df['entry_type'] == 'Sea Going']) if 'entry_type' in entries_df.columns else 0,
        'Port Entries': len(entries_df[entries_df['entry_type'] == 'In Port']) if 'entry_type' in entries_df.columns else 0
    }
    
    signatures = ['Immigration Officer', 'Seaman Signature', 'Date']
    
    return exporter.export_dataframe_to_html_pdf(
        df=export_df,
        title="Country Movement Log",
        subtitle=f"Immigration Record - {user_name}",
        info_data=info_data,
        statistics=statistics,
        filename=f"country_log_{user_name.replace(' ', '_')}.html",
        signatures=signatures
    )

def export_ship_log_pdf(entries_df: pd.DataFrame, ship_name: str = ""):
    """Export ship log entries as PDF"""
    exporter = PDFExporter()
    
    if entries_df.empty:
        st.warning("No ship log entries to export")
        return
    
    # Format dataframe for export
    export_df = entries_df.copy()
    
    # Format dates
    if 'log_date' in export_df.columns:
        export_df['log_date'] = pd.to_datetime(export_df['log_date']).dt.strftime('%Y-%m-%d')
    
    # Select and rename columns
    display_columns = {
        'log_date': 'Date',
        'log_type': 'Log Type',
        'entry_content': 'Entry Details'
    }
    
    available_columns = {k: v for k, v in display_columns.items() if k in export_df.columns}
    export_df = export_df[list(available_columns.keys())].rename(columns=available_columns)
    
    info_data = {
        'Vessel Name': ship_name,
        'Total Entries': len(entries_df),
        'Export Date': datetime.now().strftime('%Y-%m-%d'),
        'Period': f"{entries_df['log_date'].min()} to {entries_df['log_date'].max()}" if 'log_date' in entries_df.columns else "N/A"
    }
    
    # Count log types
    log_type_counts = entries_df['log_type'].value_counts() if 'log_type' in entries_df.columns else {}
    statistics = {
        'Total Entries': len(entries_df),
        **{f"{log_type} Entries": count for log_type, count in log_type_counts.head(3).items()}
    }
    
    signatures = ['Master', 'Chief Officer', 'Date']
    
    return exporter.export_dataframe_to_html_pdf(
        df=export_df,
        title="Ship's Log",
        subtitle=f"Official Log - {ship_name}",
        info_data=info_data,
        statistics=statistics,
        filename=f"ship_log_{ship_name.replace(' ', '_')}.html",
        signatures=signatures
    )

def export_risk_assessment_pdf(assessment_data: Dict[str, Any], assessment_name: str = ""):
    """Export risk assessment as PDF"""
    exporter = PDFExporter()
    
    # Create a custom template for risk assessments
    custom_styles = """
    .risk-matrix {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 5px;
        margin: 20px 0;
        max-width: 400px;
    }
    
    .risk-cell {
        padding: 10px;
        text-align: center;
        border: 1px solid #333;
        font-weight: bold;
    }
    
    .risk-low { background-color: #4CAF50; color: white; }
    .risk-medium { background-color: #FF9800; color: white; }
    .risk-high { background-color: #F44336; color: white; }
    
    .hazard-list {
        margin: 20px 0;
    }
    
    .hazard-item {
        padding: 10px;
        margin: 5px 0;
        border-left: 4px solid #1e3a8a;
        background-color: #f8f9fa;
    }
    
    .control-measures {
        margin: 10px 0;
        padding-left: 20px;
    }
    """
    
    # Build risk assessment content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Risk Assessment - {assessment_name}</title>
        <style>
            {exporter.default_styles}
            {custom_styles}
        </style>
    </head>
    <body>
        <div class="header">
            <h1> Risk Assessment</h1>
            <h2>{assessment_name}</h2>
        </div>
        
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Assessment Date</div>
                <div class="info-value">{datetime.now().strftime('%Y-%m-%d')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Assessor</div>
                <div class="info-value">{assessment_data.get('assessor', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Vessel/Location</div>
                <div class="info-value">{assessment_data.get('location', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Review Date</div>
                <div class="info-value">{assessment_data.get('review_date', 'N/A')}</div>
            </div>
        </div>
        
        <div class="hazard-list">
            <h3>Identified Hazards and Control Measures</h3>
    """
    
    # Add hazards and control measures
    hazards = assessment_data.get('hazards', [])
    for hazard in hazards:
        risk_class = 'risk-low'
        if hazard.get('risk_level', '').lower() == 'medium':
            risk_class = 'risk-medium'
        elif hazard.get('risk_level', '').lower() == 'high':
            risk_class = 'risk-high'
        
        html_content += f"""
        <div class="hazard-item">
            <h4>{hazard.get('name', 'Unnamed Hazard')} 
                <span class="risk-cell {risk_class}" style="display: inline-block; padding: 2px 8px; margin-left: 10px;">
                    {hazard.get('risk_level', 'Unknown').upper()}
                </span>
            </h4>
            <p><strong>Description:</strong> {hazard.get('description', 'No description provided')}</p>
            <div class="control-measures">
                <strong>Control Measures:</strong>
                <ul>
        """
        
        for measure in hazard.get('control_measures', []):
            html_content += f"<li>{measure}</li>"
        
        html_content += """
                </ul>
            </div>
        </div>
        """
    
    html_content += f"""
        </div>
        
        <div class="signature-section">
            <div class="signature-box">
                <div style="height: 40px;"></div>
                <div class="signature-label">Assessor Signature</div>
            </div>
            <div class="signature-box">
                <div style="height: 40px;"></div>
                <div class="signature-label">Master Approval</div>
            </div>
            <div class="signature-box">
                <div style="height: 40px;"></div>
                <div class="signature-label">Date</div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Seamans Book Cloud - Risk Assessment Tool</p>
            <p>Created on {datetime.now().strftime('%Y-%m-%d at %H:%M')}</p>
        </div>
    </body>
    </html>
    """
    
    # Create download button
    st.download_button(
        label=" Download Risk Assessment PDF",
        data=html_content.encode('utf-8'),
        file_name=f"risk_assessment_{assessment_name.replace(' ', '_')}.html",
        mime="text/html",
        help="Download as HTML file - open in browser and print to PDF for best results"
    )
    
    return html_content

# Example usage functions for testing
def demo_pdf_export():
    """Demo function to test PDF export functionality"""
    st.subheader("PDF Export Demo")
    
    # Create sample data
    sample_data = pd.DataFrame({
        'Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'Ship Name': ['MV Example', 'MV Example', 'MV Example'],
        'Port': ['Southampton', 'Le Havre', 'Rotterdam'],
        'Activity': ['Departure', 'Transit', 'Arrival'],
        'Sea Miles': [0, 120, 85]
    })
    
    exporter = PDFExporter()
    
    info_data = {
        'Vessel': 'MV Example',
        'Voyage': 'EX001',
        'Master': 'Captain Smith',
        'Export Date': datetime.now().strftime('%Y-%m-%d')
    }
    
    statistics = {
        'Total Distance': '205 nm',
        'Days at Sea': '3',
        'Ports Visited': '3',
        'Entries': '3'
    }
    
    if st.button("Generate Demo PDF"):
        exporter.export_dataframe_to_html_pdf(
            df=sample_data,
            title="Sample Maritime Log",
            subtitle="Demonstration Export",
            info_data=info_data,
            statistics=statistics,
            filename="demo_export.html",
            signatures=['Master', 'Chief Officer', 'Date']
        )