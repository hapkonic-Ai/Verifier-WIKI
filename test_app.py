import pytest
import json
from scraper import scrape_url
from verifier import ValidationResult, get_system_prompt
from report_generator import generate_pdf_report
from unittest.mock import patch, Mock

def test_scraper_mocked():
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = "<html><body><header>Ignore this</header><p>Main content text here.</p></body></html>"
        mock_get.return_value = mock_response
        
        text = scrape_url("http://dummy-url.com")
        assert "Main content text here." in text
        assert "Ignore this" not in text

def test_system_prompt_loading():
    prompt = get_system_prompt("Individual")
    assert "Wikipedia Editor" in prompt
    assert "WP:BIO" in prompt or "person is generally presumed to be notable" in prompt
    assert "WP:GNG" in prompt or "General Notability Guideline" in prompt

def test_pydantic_schema_validation():
    dummy_json = {
        "verdict": "Eligible",
        "summary": "They are famous.",
        "risk_score": 10,
        "acceptance_rate": 100.0,
        "areas_of_improvement": [],
        "source_evaluations": [
            {
                "url": "http://forbes.com",
                "is_reliable": True,
                "is_independent": True,
                "has_significant_coverage": True,
                "justification": "Good source",
                "accepted": True
            }
        ]
    }
    
    # This will raise validation error if the schema was built wrong
    result = ValidationResult(**dummy_json)
    assert result.risk_score == 10
    assert result.verdict == "Eligible"

def test_pdf_generation():
    dummy_json = json.dumps({
        "verdict": "Borderline",
        "summary": "Needs more sources.",
        "risk_score": 50,
        "acceptance_rate": 50.0,
        "areas_of_improvement": ["Get more PR"],
        "source_evaluations": []
    })
    
    pdf_bytes = generate_pdf_report("Test Entity", "Company", dummy_json)
    # PDF files start with %PDF magic bytes
    assert pdf_bytes.startswith(b"%PDF")
