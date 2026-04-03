import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()
class SourceEvaluation(BaseModel):
    url: str = Field(description="The original URL of the media source.")
    source_weight: str = Field(description="The strength of the source: 'Strong' (Investigative/Feature), 'Medium' (Routine/Tier-1 Deal), 'Weak' (Passing Mention), or 'None'.")
    justification: str = Field(description="A brief explanation for this weight. BE FAIR but acknowledge Tier-1 publishers like Reuters/Bloomberg.")
    accepted: bool = Field(description="Does this source contribute meaningfully? (True for Strong/Medium, False for Weak/None)")

class ValidationResult(BaseModel):
    verdict: str = Field(description="The final verdict: 'Eligible', 'Borderline', or 'Not Eligible'.")
    summary: str = Field(description="A detailed summary of why the entity meets (or fails to meet) the notability criteria based on all sources combined.")
    risk_score: int = Field(description="A score from 0 to 100 estimating the risk of Wikipedia deletion (e.g. 100 means extreme risk of deletion, 0 means bulletproof).")
    acceptance_rate: float = Field(description="The percentage (0.0 to 100.0) of provided sources that were strictly accepted under WP:GNG.")
    areas_of_improvement: List[str] = Field(description="Specific actionable tips on what type of PR or coverage is still needed if they fall short of notability.")
    source_evaluations: List[SourceEvaluation] = Field(description="Individual evaluations of each provided media source.")

def load_guideline(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), 'guidelines', filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return f"FAILED TO LOAD {filename}"

def get_system_prompt(entity_type: str) -> str:
    gng_text = load_guideline('gng.txt')
    
    base_prompt = f"""
    You are an expert Wikipedia Editor and Administrator specializing in Notability Guidelines (WP:N).
    Your task is to evaluate whether a proposed entity meets Wikipedia's strict inclusion criteria based ONLY on the provided media sources.
    
    --- PRIMARY GUIDELINE ---
    {gng_text}
    -------------------------
    
    CRITICAL SCORING LOGIC FOR 'source_weight':
    You must categorize each source by its weight for Wikipedia success:
    - 'Strong': Deep-dive investigative features primarily focuses on the subject, unauthorized biographies, or peer-reviewed academic profiles.
    - 'Medium': Routine but reliable business news from Tier-1 Media (Reuters, Bloomberg, FT, WSJ, NYT), major industry-leading magazines reporting on non-trivial contracts, or extensive non-primary profiles. 
    - 'Weak': Specialized industry mentions, passing quotes in broader trend pieces, or reliable but brief reports.
    - 'None': Press releases, syndicated wire churnalism (ANI/PTI), interviews, or self-published content.
    
    CRITICAL OUTPUT INSTRUCTIONS FOR 'areas_of_improvement':
    You must provide 3 to 4 enterprise-grade Public Relations & Communications consulting directives. 
    DO NOT give generic advice like 'get more news'. Provide highly advanced, actionable strategy points for a premier PR agency advising a high-value corporate client. 
    Examples of expected style:
    - 'Orchestrate a peer-reviewed academic case study on the organization's unique operational logistics to bypass routine tech press and establish WP:CORP.'
    - 'Pivot media outreach away from funding/M&A announcements; pitch an exclusive, unauthorized deep-dive feature to Tier-1 investigative journalists at WSJ, Forbes, or Bloomberg.'
    - 'Halt the reliance on PRNewswire and ANI syndicated feeds, as Wikipedia administrators actively blacklist "churnalism". Instead, secure organic mentions in independent macroeconomic trend reports.'
    
    Think carefully. Provide a step-by-step thinking process in your analysis summary. Be harsh and strict.
    Provide exact JSON formatting matching the requested schema.
    """
    
    if entity_type == "Individual":
        base_prompt += "\n--- SPECIFIC GUIDELINES ---\n" + load_guideline('bio.txt')
    elif entity_type == "Company/Organization":
        base_prompt += "\n--- SPECIFIC GUIDELINES ---\n" + load_guideline('org.txt')
    elif entity_type == "Group/Band":
        base_prompt += "\n--- SPECIFIC GUIDELINES ---\n" + load_guideline('band.txt')
    
    return base_prompt

def verify_notability(profile: str, entity_type: str, sources_text: dict) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return '{"error": "GEMINI_API_KEY is not set in the environment or .env file."}'
        
    client = genai.Client(api_key=api_key)
    # the new standard is gemini-2.5-flash or gemini-2.0-flash
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") 
    
    prompt = f"Entity Profile:\n{profile}\n\nEntity Type: {entity_type}\n\n--- MEDIA SOURCES ---\n"
    for url, text in sources_text.items():
        if text:
            trimmed_text = text[:10000] 
        else:
            trimmed_text = "[FAILED TO SCRAPE CONTENT or ACCESS BLOCKED]"
            
        prompt += f"\n[SOURCE URL]: {url}\n[CONTENT]: {trimmed_text}\n"
        
    prompt += "\n--- END SCENARIO ---\nPlease evaluate the sources and determine if this entity can have a Wikipedia page. Return the exact JSON schema requested."
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=get_system_prompt(entity_type),
                response_mime_type="application/json",
                response_schema=ValidationResult,
                temperature=0.0  # Force strictly deterministic output
            )
        )
        
        # Enforce strict mathematical truth for metrics in Python
        data = json.loads(response.text)
        sources = data.get("source_evaluations", [])
        
        if sources:
            total_sources = len(sources)
            weighted_score = 0
            count_strong = 0
            count_medium = 0
            count_weak = 0
            
            for s in sources:
                weight = s.get("source_weight", "None")
                if weight == "Strong":
                    points = 25
                    count_strong += 1
                elif weight == "Medium":
                    points = 12
                    count_medium += 1
                elif weight == "Weak":
                    points = 4
                    count_weak += 1
                else:
                    points = 0

                weighted_score += points
                # Auto-sync 'accepted' checkbox for UI clarity
                s["accepted"] = True if weight in ["Strong", "Medium"] else False
            
            # Mathematical Acceptance Probability Calculation
            # 60+ points (e.g. 3 Strong) = High Success
            # 40-59 points (e.g. 2 Strong + 1 Medium or 4-5 Medium) = Medium Success
            # <40 points = Low Success
            
            prob = min(95, weighted_score * 1.5) # Scale to percentage
            if weighted_score >= 60:
                verdict = "Eligible - High Probability of Success"
                risk = max(5, 100 - weighted_score)
            elif weighted_score >= 40:
                verdict = "Borderline - Medium Probability of Success"
                risk = 100 - weighted_score
            elif weighted_score >= 15:
                verdict = "Borderline - High Deletion Risk"
                risk = 100 - weighted_score
            else:
                verdict = "Not Eligible - Do Not Create"
                risk = 95
                
            # Overwrite metrics with hard math
            data["risk_score"] = int(risk)
            data["verdict"] = verdict
            data["acceptance_rate"] = round((weighted_score / (total_sources * 25)) * 100 if total_sources > 0 else 0, 2)
            
            # Injecting Probability as a hidden value for the text summarizing part
            data["summary"] = f"[Mathematical Probability: {int(prob)}%] " + data.get("summary", "")
                
        return json.dumps(data)
    except Exception as e:
        return f'{{\n  "error": "{str(e)}"\n}}'
