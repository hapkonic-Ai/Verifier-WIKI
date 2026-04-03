from fpdf import FPDF
import json

def clean_text(text):
    """Safely encodes text to latin-1 to avoid FPDF character errors."""
    if not text:
        return ""
    return str(text).encode('latin-1', 'ignore').decode('latin-1')

def truncate_unbroken(text, max_len=60):
    """Truncates violently long continuous strings like URLs."""
    if len(str(text)) > max_len:
        return str(text)[:max_len] + "..."
    return str(text)

def generate_pdf_report(entity_name: str, entity_type: str, raw_json: str) -> bytearray:
    data = json.loads(raw_json)
    
    pdf = FPDF()
    pdf.add_page()
    
    # Enable automatic page breaks
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("helvetica", "B", 16)
    
    # Title
    title = clean_text(f"Wikipedia Notability Report: {entity_name}")
    pdf.multi_cell(0, 10, title)
    pdf.set_font("helvetica", "", 12)
    pdf.multi_cell(0, 10, clean_text(f"Entity Type: {entity_type}"))
    pdf.ln(5)
    
    # Metrics
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Evaluation Metrics", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    
    verdict = data.get("verdict", "Unknown")
    pdf.cell(0, 10, f"Final Verdict: {verdict}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Risk Score (0-100): {data.get('risk_score', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Acceptance Rate: {data.get('acceptance_rate', 'N/A')}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Summary
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    
    pdf.multi_cell(0, 6, clean_text(data.get("summary", "")))
    pdf.ln(5)
    
    # Areas of Improvement
    areas = data.get("areas_of_improvement", [])
    if areas:
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Areas of Improvement", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 11)
        for area in areas:
            pdf.multi_cell(0, 6, clean_text(f"- {area}"))
        pdf.ln(5)
        
    # Source Breakdown
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Source Breakdown", new_x="LMARGIN", new_y="NEXT")
    
    sources = data.get("source_evaluations", [])
    for idx, raw_src in enumerate(sources):
        pdf.set_font("helvetica", "B", 12)
        url = raw_src.get('url', 'Unknown')
        
        # safely handle super long URLs so they don't break horizontal space
        display_url = truncate_unbroken(url, max_len=60)
        
        pdf.multi_cell(0, 8, clean_text(f"Source {idx+1}: {display_url}"))
        
        pdf.set_font("helvetica", "", 10)
        accepted = "YES" if raw_src.get("accepted") else "NO"
        pdf.cell(0, 6, f"Accepted: {accepted}", new_x="LMARGIN", new_y="NEXT")
        pdf.multi_cell(0, 6, clean_text(f"Reliable: {raw_src.get('is_reliable')} | Independent: {raw_src.get('is_independent')} | Significant: {raw_src.get('has_significant_coverage')}"))
        
        # Justification
        pdf.multi_cell(0, 6, clean_text(f"Justification: {raw_src.get('justification', '')}"))
        pdf.ln(4)
        
    # Return byte string
    return pdf.output()
