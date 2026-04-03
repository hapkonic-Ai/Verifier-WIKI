# Wikipedia Notability Verifier

A tool to evaluate if an individual, company, or group meets Wikipedia's strict Notability Guidelines (WP:N) using Gemini LLM.

## Setup Instructions

1. **Install Dependencies:**
   Make sure you have Python 3.9+ installed.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and add your Gemini API Key.
   ```bash
   cp .env.example .env
   # Edit .env and set GEMINI_API_KEY
   ```

3. **Run the Application:**
   ```bash
   streamlit run app.py
   ```

## How It Works

- The tool acts as a strict Wikipedia Editor based on the General Notability Guideline (WP:GNG).
- It evaluates media sources based on Reliability, Independence, and Significant Coverage.
- It applies specific sub-rules (WP:BIO for people, WP:ORG for companies, WP:BAND for groups).
