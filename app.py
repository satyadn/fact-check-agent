import streamlit as st
import fitz
import google.generativeai as genai
import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


# if st.button("Test Search"):

#     result = tavily.search(
#         query="India population 2025"
#     )

#     st.write(result)


st.title("Fact Check Agent")

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"]
)

if uploaded_file:

    pdf_text = ""

    pdf = fitz.open(
        stream=uploaded_file.read(),
        filetype="pdf"
    )

    for page in pdf:
        pdf_text += page.get_text()
   #  st.subheader("Extracted Text")

   #  st.text(pdf_text[:5000])

    st.subheader("Extracting Claims...")

    claim_prompt = f"""
    You are an expert claim extraction system.

    Your task is to extract EVERY factual statement that can be verified or disproven using web sources.

    Include:
    - Statistics
    - Numbers
    - Percentages
    - Dates
    - Financial figures
    - Technical metrics
    - Historical facts
    - Scientific facts
    - Geographic facts
    - Company facts
    - Product facts
    - Records, rankings, measurements, and quantities

    Ignore ONLY:
    - Opinions
    - Personal preferences
    - Emotions
    - Instructions
    - Questions
    - Marketing slogans
    - Subjective statements

    IMPORTANT RULES:

    1. Extract ALL factual claims, even if they do not contain numbers.
    2. Do NOT skip claims because they seem obvious or common knowledge.
    3. Do NOT rewrite claims.
    4. Preserve the original wording whenever possible.
    5. Return every factual claim as a separate item.
    6. Before returning, verify that every factual statement from the input has either:
    - been included in the output, or
    - been excluded because it is an opinion, instruction, question, or subjective statement.
    7. Do not omit factual statements that are false, suspicious, or unlikely to be true.
    8. False claims are still claims and must be extracted.

    Return ONLY a numbered list.

    Do NOT provide explanations.
    Do NOT provide summaries.
    Do NOT provide introductions.
    Do NOT provide conclusions.
    Do NOT ask follow-up questions.

    Text:
    {pdf_text}   
    """

    claims_response = model.generate_content(
        claim_prompt
    )

    claims = claims_response.text

    claim_list = []

    for line in claims.split("\n"):

      line = line.strip()

      if not line:
         continue

      if ". " in line:
         line = line.split(". ", 1)[1]

      claim_list.append(line)

   #  st.subheader("Claim List")
   #  st.write(claim_list)

    all_evidence = ""

    for claim in claim_list:

      search_results = tavily.search(
         query=claim,
         max_results=3
      )

      all_evidence += f"\n\nCLAIM: {claim}\n"
      all_evidence += str(search_results)

   #  st.subheader("Web Evidence")

   #  st.text(all_evidence[:10000])

   #  st.write(claims)

   #  st.subheader("Searching Web...")
    with st.spinner("Fact checking document..."):
      st.subheader("Fact Checking...")

      verify_prompt = f"""
      You are a professional fact-checking system.

      Use ONLY the supplied web evidence.

      For each claim return exactly in this format:

      ### Claim
      <claim>

      **Status:** VERIFIED / INACCURATE / FALSE

      **Correct Fact:**
      <correct fact>

      **Reason:**
      <short explanation>

      Claims:
      {claims}

      Web Evidence:
      {all_evidence}
      """

      result = model.generate_content(
         verify_prompt
      )

      st.markdown(result.text)