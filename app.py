import streamlit as st
import json
import time
import os
from scraper import scrape_url
from verifier import verify_notability
from pdf_builder import create_pdf_safe
from search_engine import perform_search

st.set_page_config(page_title="Wikipedia Notability Verifier", page_icon="🎓", layout="wide")

st.title("Wikipedia Notability Verifier 🎓")
st.markdown("Analyze an entity's media coverage to determine if it meets Wikipedia's strict Notability Guidelines (WP:N).")

# Warning if API key is not set
if not os.getenv("GEMINI_API_KEY"):
    st.warning("⚠️ **GEMINI_API_KEY is not set.** Please add it to your `.env` file or environment variables before running.")

# Initialize session state for URLs
if 'selected_urls' not in st.session_state:
    st.session_state.selected_urls = []

# Sidebar for Input
with st.sidebar:
    st.header("Entity Information")
    entity_name = st.text_input("Name", placeholder="e.g., Jane Doe, Acme Corp...")
    entity_type = st.selectbox("Type", ["Individual", "Company/Organization", "Group/Band"])
    profile = st.text_area("Profile/Description", placeholder="A brief background about the entity...")

tab1, tab2 = st.tabs(["🔍 Media Discovery Engine", "🎓 Verification Engine"])

with tab1:
    st.header("Discover Media Sources")
    st.write("Use our built-in DuckDuckGo search engine to scrape the web for the most relevant articles about your entity.")
    
    if st.button("Search Web for Sources"):
        if not entity_name:
            st.error("Please enter the Entity Name in the sidebar first.")
        else:
            with st.spinner(f"Scouring the web for news featuring '{entity_name}'..."):
                results = perform_search(entity_name, max_results=12)
                st.session_state.current_search_results = results
                
    # If we have search results stored in state (or just generated)
    if 'current_search_results' in st.session_state and st.session_state.current_search_results:
        st.success(f"Found {len(st.session_state.current_search_results)} potential articles.")
        
        with st.form("search_results_form"):
            st.write("Select the articles you want to evaluate:")
            
            for idx, res in enumerate(st.session_state.current_search_results):
                title = res.get('title', 'Unknown Title')
                url = res.get('href', '')
                body = str(res.get('body', ''))[:150] + "..."
                
                st.markdown(f"**[{title}]({url})**")
                st.caption(body)
                st.checkbox(f"Add to verification list", key=f"select_{idx}", value=False)
                st.divider()
                
            submitted = st.form_submit_button("Add Selected to Verification Engine")
            if submitted:
                chosen_urls = []
                for idx, res in enumerate(st.session_state.current_search_results):
                    if st.session_state.get(f"select_{idx}", False):
                        chosen_urls.append(res.get('href'))
                        
                if chosen_urls:
                    added_count = 0
                    for u in chosen_urls:
                        if u not in st.session_state.selected_urls:
                            st.session_state.selected_urls.append(u)
                            added_count += 1
                    if added_count > 0:
                        st.success(f"Added {added_count} new URLs! Switch to the **Verification Engine** tab to proceed.")
                    else:
                        st.info("No new URLs were added (they might already be in your list).")
                else:
                    st.warning("No URLs selected. Check the boxes above first.")

with tab2:
    st.header("Assess Notability")
    st.write("URLs ready for evaluation. You can manually edit, remove, or paste additional links below:")
    
    # We display them in a text area so the user can easily manage them manually.
    default_text = "\n".join(st.session_state.selected_urls)
    urls_input = st.text_area("URLs (One per line)", value=default_text, height=250, placeholder="https://forbes.com/article...\nhttps://techcrunch.com/article...")
    
    if st.button("Verify Notability", type="primary"):
        if not entity_name or not profile or not urls_input:
            st.error("Please fill out all fields (Name, Profile, and URLs) to begin Verification.")
        else:
            urls = [url.strip() for url in urls_input.split("\n") if url.strip()]
            
            if not urls:
                st.error("Please provide at least one valid URL.")
            else:
                with st.spinner("Scraping and analyzing sources... This may take a minute."):
                    # 1. Scrape URLs
                    sources_data = {}
                    progress_bar = st.progress(0)
                    
                    for i, url in enumerate(urls):
                        text = scrape_url(url)
                        sources_data[url] = text
                        progress_bar.progress((i + 1) / len(urls))
                    
                    # 2. Verify Notability
                    st.info("Analyzing sources using Gemini against Wikipedia's Inclusion rules...")
                    raw_result = verify_notability(profile, entity_type, sources_data)
                    
                    try:
                        result = json.loads(raw_result)
                        
                        if "error" in result:
                            st.error(f"Error: {result['error']}")
                        else:
                            st.success("Analysis Complete!")
                            
                            # Verdict
                            verdict = result.get("verdict", "Unknown")
                            color = "green" if "Eligible" in verdict and "Not" not in verdict else "orange" if "Borderline" in verdict else "red"
                            st.markdown(f"## Verdict: :{color}[{verdict}]")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            # Metrics
                            risk = result.get("risk_score", 95)
                            prob = 100 - risk
                            col1.metric("Success Probability", f"{prob}%")
                            col2.metric("Risk Score", f"{risk}/100", delta_color="inverse")
                            
                            acc = result.get("acceptance_rate", 0.0)
                            col3.metric("GNG Acceptance", f"{acc}%")
                            
                            st.divider()
                            
                            # Download PDF
                            try:
                                pdf_bytes = create_pdf_safe(entity_name, entity_type, raw_result)
                                st.download_button(
                                    label="📄 Download Official PDF Report",
                                    data=pdf_bytes,
                                    file_name=f"{entity_name.replace(' ', '_')}_notability_report.pdf",
                                    mime="application/pdf",
                                    type="primary",
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error(f"Failed to generate PDF Report: {e}")
                            
                            st.divider()
                            
                            # Summary
                            st.markdown("#### Evaluation Summary")
                            st.write(result.get("summary", ""))
                            
                            # Areas of Improvement
                            areas = result.get("areas_of_improvement", [])
                            if areas:
                                st.markdown("#### Areas for Improvement")
                                for area in areas:
                                    st.markdown(f"- {area}")
                            
                            st.divider()
                            
                            # Sources Evaluation
                            st.markdown("#### Source Intelligence Breakdown")
                            for source in result.get("source_evaluations", []):
                                weight = source.get("source_weight", "None")
                                icon = "🟢" if weight == "Strong" else "🔵" if weight == "Medium" else "🟡" if weight == "Weak" else "🔴"
                                
                                with st.expander(f"{icon} {weight.upper()}: {source.get('url', 'Unknown')}"):
                                    st.markdown(f"**Justification:** {source.get('justification')}")
                                    st.caption(f"Technical Weight: {weight}")
                                    
                    except json.JSONDecodeError:
                        st.error("Failed to parse the response from Gemini. The model might have returned an invalid format.")
                        with st.expander("Raw Output / Error Data"):
                            st.text(raw_result)
