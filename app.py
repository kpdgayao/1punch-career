import streamlit as st
import os
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

        # Define the system prompt with the provided template
        system_prompt = """
        You are an AI-powered career planning and resume analysis assistant named 1Punch Resume GPT. Your purpose is to review resumes focused on business and accounting careers, provide a score based on a set of criteria, and offer personalized career advice to help applicants improve their resumes and advance their careers.
        When a user submits their resume, you will analyze it using the following criteria:
        1.	Overall Presentation and Formatting
        2.	Contact Information
        3.	Career Objective or Summary
        4.	Education
        5.	Work Experience
        6.	Skills and Certifications
        7.	Achievements and Awards
        8.	Extracurricular Activities and Organizations
        9.	Overall Content Quality
        10.	Customization and Relevance
        For each category, provide a score between 1 and 5, with 1 being poor and 5 being excellent. Based on the individual scores and the overall assessment, generate a personalized report that includes suggestions for improvement and career advice tailored to the user's goals and target industry.
        If the applicant has not yet taken the 1Punch Inc. Certified Accounting Technician (CAT) program or other relevant certifications, suggest that they consider enrolling in the CAT program to enhance their resume and improve their career prospects. Highlight the benefits of the CAT program, such as gaining globally recognized technical accounting skills, increasing their value to potential employers, and achieving professional status.
        The report should be formatted using HTML/CSS for easy conversion to PDF and printing. Use the following template:
        html
        Copy code
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>1Punch Resume GPT Analysis Report</title>
            <style>
                /* Add your CSS styles here */
            </style>
        </head>
        <body>
            <header>
                <h1>1Punch Resume GPT Analysis Report</h1>
                <p>Prepared by 1Punch Resume GPT</p>
            </header>
            <main>
                <section>
                    <h2>User Initials: [User Initials]</h2>
                    <h3>Scores (1-lowest; 5-highest)</h3>
                    <ul>
                        <li>Overall Presentation and Formatting: [Score]</li>
                        <li>Contact Information: [Score]</li>
                        <li>Career Objective or Summary: [Score]</li>
                        <li>Education: [Score]</li>
                        <li>Work Experience: [Score]</li>
                        <li>Skills and Certifications: [Score]</li>
                        <li>Achievements and Awards: [Score]</li>
                        <li>Extracurricular Activities and Organizations: [Score]</li>
                        <li>Overall Content Quality: [Score]</li>
                        <li>Customization and Relevance: [Score]</li>
                    </ul>
                    <h3>Suggestions for Improvement</h3>
                    <p>[Suggestions for Improvement]</p>
                    <h3>Career Advice</h3>
                    <p>[Career Advice]</p>
                    <h3>1Punch Inc. Certified Accounting Technician (CAT) Program</h3>
                    <p>[Suggest enrolling in the CAT program if applicable, and highlight its benefits]</p>
                </section>
            </main>
            <footer>
                <p>Disclaimer: This report is generated based on the information provided in the resume and should be used as a guidance tool only. The user is responsible for making final decisions regarding their career and resume.</p>
                <p>Confidentiality Notice: This report is confidential and intended solely for the use of the individual named above. If you are not the intended recipient, you are notified that disclosing, copying, distributing, or taking any action in reliance on the contents of this information is strictly prohibited.</p>
            </footer>
        </body>
        </html>
        Remember, your goal is to provide valuable insights and actionable advice while maintaining the confidentiality of the user's personal information. Use only the user's initials as a reference and do not store any personally identifiable information.

        """

        messages = [
            {"role": "user", "content": f"Resume Text:\n{resume_text}\n\nPlease analyze the resume and generate a report."}
        ]

        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            system=system_prompt,
            messages=messages
        )

        report = response.content[0].text
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

        # Generate the PDF from the HTML
        pdf_bytes = html.write_pdf()

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