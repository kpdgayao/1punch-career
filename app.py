import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
import uuid
import io
import PyPDF2
import anthropic
from weasyprint import HTML, CSS
import logging
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

# Set up Anthropic API client
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
anthropic_api_url = "https://api.anthropic.com/v1/messages"

# Set up Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_api_key = os.getenv("SUPABASE_API_KEY")
supabase_client = create_client(supabase_url, supabase_api_key)

@st.cache_data(show_spinner=False)
def extract_text_from_pdf(file):
    try:
        # Set a file size limit (e.g., 5MB)
        max_size = 5 * 1024 * 1024
        if file.size > max_size:
            st.warning("File size exceeds the limit of 5MB. Please upload a smaller file.")
            return None

        # Create a BytesIO object from the uploaded file
        file_bytes = io.BytesIO(file.read())

        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(file_bytes)

        # Extract text from each page of the PDF
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        return text
    except Exception as e:
        st.error(f"Error occurred during text extraction: {str(e)}")
        return None

@st.cache_data(show_spinner=False)
def process_resume_data(resume_text):
    try:
        # Use Anthropic API to process the resume data
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        client = anthropic.Client(api_key=anthropic_api_key)

        system_prompt = """
        <html>
        <head>
            <style>
            /* General Styling */
            body {
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; /* More modern font choice */
                font-size: 14px;  /* Slightly larger for readability */
                line-height: 1.6; /* Improved line height for better readability */
                margin: 20px;   /* Margins on all sides for breathing room */
                color: #333;
                background-color: #fff; /* White background for a clean look */
            }

            /* Heading Styling */
            h1 {
                font-size: 32px;    
                font-weight: 600;     /* Slightly less bold */
                margin-bottom: 20px;  /* More space below main heading */
                color: #007bff;     /* Blue accent color */
                text-align: center;
                text-transform: none; /* Remove uppercase for a more refined look */
            }

            h2 {
                font-size: 24px;
                font-weight: 600;
                margin-top: 40px;
                margin-bottom: 15px;
                color: #333; /* Darker color for contrast */
                border-bottom: 2px solid #eee; /* Subtle border */
            }

            h3 {
                font-size: 18px;
                font-weight: 500;  /* Slightly lighter weight */
                margin-top: 30px;
                margin-bottom: 10px;
                color: #555;       /* Gray for section headings */
            }

            /* Paragraph and List Styling */
            p {
                margin-bottom: 20px;
                text-align: justify; /* Justify text for a more formal look */
            }

            ul, ol {
                margin-bottom: 20px;
                padding-left: 40px; /* Increase indentation for lists */
            }

            li {
                margin-bottom: 5px;
            }

            /* Emphasis Styling */
            strong {
                font-weight: 600; /* Consistent bold style */
            }

            em {
                font-style: italic;
            }

            /* Score Item Styling */
            .scores {
                margin-bottom: 40px;
                padding: 25px; 
                background-color: #f8f9fa; /* Light gray background */
                border: 1px solid #eee;  /* Subtle border */
                border-radius: 8px;       /* Softer corners */
            }

            .score-item {
                margin-bottom: 15px;
                padding-left: 15px;
                border-left: 4px solid #007bff;  /* Blue accent */
            }

            /* Disclaimer and Confidential Styling */
            .disclaimer, .confidential {
                font-size: 12px;
                color: #6c757d;  /* Gray for legal text */
                margin-top: 50px;
                padding: 15px;
                background-color: #fff; 
                border: 1px solid #dee2e6; /* Light gray border */
                border-radius: 8px;
            }

            /* Print Styling */
            @media print {
                body {
                    background-color: #fff;
                }
            }
            </style>
        </head>
        <body>
            <h1>1Punch Resume GPT Analysis Report</h1>
            <p>Prepared by 1Punch Inc.</p>

            <h2>User Initials: [User Initials]</h2>

            <h3>Scores:</h3>
            <ol class="scores">
                <li class="score-item">Overall Presentation and Formatting: [Score]</li>
                <li class="score-item">Contact Information: [Score]</li>
                <li class="score-item">Career Objective or Summary: [Score]</li>
                <li class="score-item">Education: [Score]</li>
                <li class="score-item">Work Experience: [Score]</li>
                <li class="score-item">Skills and Certifications: [Score]</li>
                <li class="score-item">Achievements and Awards: [Score]</li>
                <li class="score-item">Extracurricular Activities and Organizations: [Score]</li>
                <li class="score-item">Overall Content Quality: [Score]</li>
                <li class="score-item">Customization and Relevance: [Score]</li>
            </ol>

            <h3>Feedback:</h3>
            <p>[Provide specific, actionable feedback for each category. Be direct but constructive. Offer clear examples and suggestions for improvement. Use HTML tags to format the content, such as <strong>, <em>, <ul>, <ol>, <li> for lists, and <br> for line breaks.]</p>

            <h3>Strengths:</h3>
            <p>[Highlight 2-3 key strengths of the resume. Focus on unique selling points, impactful achievements, and relevant skills/experience. Use HTML tags to format the content, such as <strong>, <em>, <ul>, <ol>, <li> for lists, and <br> for line breaks.]</p>

            <h3>Areas for Improvement:</h3>
            <p>[Identify 2-3 critical areas where the resume falls short. Provide targeted recommendations to address these weaknesses and elevate the resume's impact. Use HTML tags to format the content, such as <strong>, <em>, <ul>, <ol>, <li> for lists, and <br> for line breaks.]</p>

            <h3>ATS Optimization:</h3>
            <p>[Assess how well the resume is optimized for Applicant Tracking Systems (ATS). Offer tips to improve keyword relevance, formatting, and overall ATS compatibility. Use HTML tags to format the content, such as <strong>, <em>, <ul>, <ol>, <li> for lists, and <br> for line breaks.]</p>

            <h3>Target Industry/Role Alignment:</h3>
            <p>[Evaluate how effectively the resume aligns with the candidate's target industry and desired roles. Suggest ways to better tailor the content and messaging to resonate with employers in their chosen field. Use HTML tags to format the content, such as <strong>, <em>, <ul>, <ol>, <li> for lists, and <br> for line breaks.]</p>

            <h3>Career Trajectory Insights:</h3>
            <p>[Based on the candidate's education, skills, and experience, provide insights into potential career paths, growth opportunities, and any skill gaps or areas for professional development. Use HTML tags to format the content, such as <strong>, <em>, <ul>, <ol>, <li> for lists, and <br> for line breaks.]</p>

            <h3>1Punch CAT Program Recommendation:</h3>
            <p>[If the candidate has not completed the 1Punch Certified Accounting Technician (CAT) program and could benefit from this credential, emphasize the advantages of enrolling. Explain how the CAT program can boost their resume, expand their knowledge, and open up new career possibilities. Use HTML tags to format the content, such as <strong>, <em>, <ul>, <ol>, <li> for lists, and <br> for line breaks.]</p>

            <h3>Customized Career Advice:</h3>
            <p>[Offer 2-3 personalized career tips based on the candidate's unique profile and aspirations. This could include networking strategies, skill-building ideas, job search advice, or interview preparation tips. Use HTML tags to format the content, such as <strong>, <em>, <ul>, <ol>, <li> for lists, and <br> for line breaks.]</p>

            <h3>Next Steps:</h3>
            <p>[Provide a concise summary of the most important actions the candidate should take to improve their resume and advance their career. Encourage them to stay proactive, adaptable, and committed to professional growth. Use HTML tags to format the content, such as <strong>, <em>, <ul>, <ol>, <li> for lists, and <br> for line breaks.]</p>

            <p class="disclaimer">Disclaimer: This report is based solely on the information provided in the candidate's resume. The insights and recommendations offered are for guidance purposes only. The candidate is ultimately responsible for all career decisions and outcomes.</p>

            <p class="confidential">Confidentiality Notice: This report is confidential and intended solely for the use of the individual candidate. Unauthorized disclosure, copying, distribution, or reliance on the contents herein is strictly prohibited.</p>
        </body>
        </html>

        [IMPORTANT INSTRUCTIONS]
        - Start the report directly with the "1Punch Resume GPT Analysis Report" heading.
        - For sections that require lists (e.g., Feedback, Strengths, Areas for Improvement), use appropriate HTML tags such as <ul>, <ol>, and <li> to create properly formatted lists.
        - Use other relevant HTML tags like <strong>, <em>, and <br> to format and structure the content effectively.
        - Ensure that the scores, feedback, and recommendations are specific, actionable, and aligned with the candidate's resume and career aspirations.
        """

        messages = [
            {"role": "user", "content": f"Resume Text:\n{resume_text}\n\nPlease analyze the resume and generate a report using the provided HTML/CSS template. Do not include any introductory text or preamble before the report."}
        ]

        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            system=system_prompt,
            messages=messages
        )

        report = response.content[0].text
        print(f"Generated Report: {report}")  # Print the generated report for debugging

        return report

    except anthropic.BadRequestError as e:
        st.error(f"Bad Request Error occurred while processing the resume data. Error details: {str(e)}")
        return None
    except anthropic.APIError as e:
        st.error(f"API Error occurred while processing the resume data. Error details: {str(e)}")
        logging.error(f"Anthropic API Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while processing the resume data. Error details: {str(e)}")
        return None

def store_resume_report(resume_report, user_initials, resume_text):
    try:
        # Store the resume report in Supabase
        resume_report_record = {
            "id": str(uuid.uuid4()),
            "report": resume_report
        }
        response = supabase_client.table("resume_reports").insert(resume_report_record).execute()

        if response:
            # Store the metadata in Supabase
            metadata_record = {
                "id": str(uuid.uuid4()),
                "resume_report_id": response.data[0]["id"],
                "user_initials": user_initials,
                "resume_text": resume_text
            }
            supabase_client.table("resume_metadata").insert(metadata_record).execute()

            st.success("Resume report and metadata stored successfully.")
        else:
            st.error("Failed to store resume report.")
    except Exception as e:
        st.error(f"Error occurred while storing resume report: {str(e)}")

def html_to_pdf(report):
    try:
        # Create an HTML object from the report string
        html = HTML(string=report)

        # Load the external CSS file
        css_path = Path("styles.css")
        with open(css_path, "r", encoding="utf-8") as file:
            css = file.read()

        # Generate the PDF from the HTML and CSS
        pdf_bytes = html.write_pdf(stylesheets=[CSS(string=css)])

        return pdf_bytes
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

def extract_user_initials(resume_report):
    try:
        # Extract the user initials from the resume report using string manipulation
        start_index = resume_report.find("User Initials: ") + len("User Initials: ")
        end_index = resume_report.find("</h2>", start_index)

        if start_index != -1 and end_index != -1:
            user_initials = resume_report[start_index:end_index].strip()
            return user_initials
        else:
            return "N/A"
    except Exception as e:
        st.error(f"Error extracting user initials: {e}")
        return "N/A"

def main():
    st.set_page_config(page_title="1Punch Resume GPT")
    st.title("1Punch Resume GPT")

    with st.expander("Upload Resume"):
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file:
        with st.spinner("Extracting resume text..."):
            resume_text = extract_text_from_pdf(uploaded_file)

        if resume_text:
            with st.spinner("Analyzing resume..."):
                resume_report = process_resume_data(resume_text)

            if resume_report:
                # Display Report in Expandable Section
                with st.expander("View Resume Analysis Report"):
                    st.markdown(
                        """
                        <style>
                        .resume-report {
                            font-family: Arial, sans-serif;
                            font-size: 14px;
                            line-height: 1.5;
                        }
                        .resume-report h1, .resume-report h2, .resume-report h3, .resume-report h4, .resume-report h5, .resume-report h6 {
                            margin-top: 20px;
                            margin-bottom: 10px;
                        }
                        .resume-report p {
                            margin-bottom: 10px;
                        }
                        .resume-report ul, .resume-report ol {
                            margin-left: 20px;
                            margin-bottom: 10px;
                        }
                        .resume-report li {
                            margin-bottom: 5px;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(resume_report, unsafe_allow_html=True)

                if resume_report:
                    with st.spinner("Storing report..."):
                        user_initials = extract_user_initials(resume_report)
                        store_resume_report(resume_report, user_initials, resume_text)
                        st.success("Resume report processed successfully.")

                    with st.spinner("Generating PDF..."):
                        try:
                            pdf_bytes = html_to_pdf(resume_report)

                            # Extract the user initials from the generated report
                            user_initials = extract_user_initials(resume_report)

                            if user_initials == "N/A":
                                file_name = "resume_analysis_report.pdf"
                            else:
                                file_name = f"{user_initials}_resume_analysis_report.pdf"

                            st.download_button(
                                label="Download PDF",
                                data=pdf_bytes,
                                file_name=file_name,
                                mime="application/pdf",
                            )
                        except Exception as e:
                            st.error(f"Error generating PDF: {e}")
                else:
                    st.error("Failed to generate resume report.")
            else:
                st.error("Failed to analyze resume.")
        else:
            st.error("Failed to extract resume text.")
    else:
        # Display a message when no file is uploaded
        st.info("Please upload a resume in PDF format.")

if __name__ == "__main__":
    main()