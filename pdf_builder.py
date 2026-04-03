from fpdf import FPDF
import json
import textwrap

def safe_encode(text):
    if not text: return ""
    return str(text).encode('latin-1', 'ignore').decode('latin-1')

def chunk_text(text, width=80):
    lines = []
    for paragraph in str(text).split('\n'):
        if not paragraph.strip():
            lines.append("")
        else:
            lines.extend(textwrap.wrap(paragraph, width=width, break_long_words=True))
    return lines

class PDF(FPDF):
    def header(self):
        # A sleek dark topbar across all pages
        self.set_fill_color(33, 37, 41) 
        self.rect(0, 0, 210, 18, 'F')
        self.set_y(5)
        self.set_x(15)
        self.set_font("helvetica", "B", 18)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, "Wikipedia Notability Verifier", new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_y(18)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def section_title(pdf, title):
    """Draws a modern corporate section headline with a subtle blue accent bar"""
    pdf.ln(8)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(33, 37, 41)
    
    x = pdf.get_x()
    y = pdf.get_y()
    pdf.set_fill_color(41, 128, 185) # Blue accent
    pdf.rect(x - 3, y + 1, 1.5, 6, 'F')
    
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

def create_pdf_safe(entity_name: str, entity_type: str, raw_json: str) -> bytearray:
    data = json.loads(raw_json)
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # --- Title Section ---
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 26)
    pdf.set_text_color(41, 128, 185) # Bright Corporate Blue
    for line in chunk_text("Wikipedia Notability Report", 50):
        pdf.cell(0, 10, safe_encode(line), new_x="LMARGIN", new_y="NEXT")
        
    pdf.set_font("helvetica", "", 16)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, safe_encode(f"Subject: {entity_name}"), new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "I", 12)
    pdf.cell(0, 6, safe_encode(f"Classification: {entity_type}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    
    # Divider Line
    pdf.set_draw_color(220, 220, 220)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    
    # --- Executive Summary ---
    section_title(pdf, "Executive Summary")
    
    pdf.set_font("helvetica", "B", 11)
    verdict = data.get("verdict", "Unknown")
    
    # Color code the verdict dynamically
    if "Safe" in verdict or "Eligible" in verdict and "Not" not in verdict:
        pdf.set_text_color(39, 174, 96) # Green
    elif "Borderline" in verdict:
        pdf.set_text_color(243, 156, 18) # Orange
    else:
        pdf.set_text_color(192, 57, 43) # Red
        
    pdf.cell(0, 6, safe_encode(f"Final Verdict: {verdict}"), new_x="LMARGIN", new_y="NEXT")
    
    # Metrics
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 11)
    
    # Calculate probability for display from the risk score
    # (High risk = 100, Low risk = 5)
    # We'll use the probability we injected into the summary if possible, 
    # or just inverse the risk score for the header.
    risk_val = data.get('risk_score', 95)
    prob_val = 100 - risk_val
    
    pdf.cell(0, 6, safe_encode(f"Success Probability: {prob_val}%"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, safe_encode(f"Risk of Deletion: {risk_val}/100"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, safe_encode(f"GNG Acceptance Rate: {data.get('acceptance_rate', 'N/A')}%"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # Summary Para
    summary = data.get("summary", "")
    pdf.set_text_color(60, 60, 60)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 6, safe_encode(summary), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
        
    # --- Strategic Improvements ---
    areas = data.get("areas_of_improvement", [])
    if areas:
        section_title(pdf, "Strategic Areas for Improvement")
        pdf.set_text_color(60, 60, 60)
        pdf.set_font("helvetica", "", 10)
        for idx, area in enumerate(areas):
            pdf.multi_cell(0, 6, safe_encode(f"• {area}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            
    # --- Source Breakdown ---
    section_title(pdf, "Source Intelligence Data")
    sources = data.get("source_evaluations", [])
    
    for idx, raw_src in enumerate(sources):
        pdf.set_font("helvetica", "B", 10)
        url = str(raw_src.get('url', 'Unknown'))
        
        # Only chunk URLs since they lack spaces and cause crashes
        pdf.set_text_color(41, 128, 185) 
        for line in chunk_text(f"[{idx+1}] {url}", 75):
            pdf.cell(0, 5, safe_encode(line), new_x="LMARGIN", new_y="NEXT")
            
        # Highlight Weight
        weight = raw_src.get("source_weight", "None")
        pdf.set_font("helvetica", "B", 10)
        
        if weight == "Strong":
            pdf.set_text_color(39, 174, 96) # Green
        elif weight == "Medium":
            pdf.set_text_color(41, 128, 185) # Blue
        elif weight == "Weak":
            pdf.set_text_color(243, 156, 18) # Orange
        else:
            pdf.set_text_color(192, 57, 43) # Red
            
        pdf.cell(0, 6, safe_encode(f"Source Weight: {weight.upper()}"), new_x="LMARGIN", new_y="NEXT")
        
        # Justification Analysis
        pdf.set_text_color(60, 60, 60)
        pdf.set_font("helvetica", "", 10)
        just = raw_src.get('justification', '')
        pdf.multi_cell(0, 5, safe_encode(f"Analysis: {just}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        
        # Internal divider line to separate large source lists seamlessly
        pdf.set_draw_color(240, 240, 240)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(3)

    # --- Legal & Disclaimers Section ---
    pdf.add_page() # Put disclaimers cleanly on their own page or at the very end
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, " Legal Disclaimers & Notability Warnings", new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(3)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    disclaimers = (
        "1. Wikipedia Administrative Authority: This document functions as an AI-powered advisory report "
        "simulating Wikipedia's strict Articles for Deletion (AfD) grading rubric. While it calculates variables "
        "rigidly based on WP:GNG, WP:CORP, and WP:BIO policies, it cannot definitively guarantee page inclusion. "
        "The ultimate consensus on notability rests exclusively with Wikipedia's volunteer administrative community.\n\n"
        
        "2. Algorithmic Scraping Limitations: Major media platforms occasionally deploy aggressive paywalls or bot "
        "protection (e.g., Cloudflare 403 Forbidden). Any URL computationally blocked during the live-scraping phase "
        "is voided and does not contribute to the Success Probability evaluation.\n\n"
        
        "3. Strict Baseline Computation: This Notability Engine operates strictly on objective, verifiable text "
        "extracted directly from the provided URLs. Extraneous public knowledge not present in the provided links is "
        "not considered during this evaluation.\n\n"
        
        "4. Confidentiality Note: This intelligence report is generated via the proprietary verification "
        "engine and is recommended for internal public relations, asset auditing, and digital strategy use only."
    )
    pdf.multi_cell(0, 6, safe_encode(disclaimers), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
