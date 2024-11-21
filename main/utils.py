import os
import pandas as pd
from django.conf import settings
import fitz  # PyMuPDF
import re
import tabula
import logging

from main.models import Feedback, Module, Question, Section
logger = logging.getLogger(__name__)



def extract_student_info_from_pdf(pdf_path, is_group=False):
    # Use tabula to extract tables from the first page of the PDF
    tables = tabula.read_pdf(pdf_path, pages=1, multiple_tables=True)

    student_info = []

    if tables:
        # Assuming the first table is the one that contains the student data
        # You may need to inspect the tables to ensure this is correct
        table = tables[0]
        logger.info(table)

        first_name = None
        last_name = None
        student_number = None
        group_number = None 

        logger.info(f"is_group: {is_group}")    

        # Assuming the table has columns for first name, last name, and student number
        if is_group:
            for index, row in table.iterrows():
                
                if index == 0:
                    continue
                
                logger.error(f"row: {row}")  

                last_name = row[0]
                first_name = row[1]
                student_number = row[2]
                group_number = row[3]
                logger.info(f"first_name: {first_name}, last_name: {last_name}, student_number: {student_number}, group_number: {group_number}")
                student_info.append({
                    "first_name": first_name,
                    "last_name": last_name,
                    "student_number": student_number,
                    "group_number": group_number
                })
        else:
            for index, row in table.iterrows():
                # Extract the first name, last name, and student number
                if row[0] == 'First Name':
                    first_name = row[1]
                elif row[0] == 'Last Name':
                    last_name = row[1]
                elif row[0] == 'Student ID':
                    student_number = row[1]
                logger.info(f"first_name: {first_name}, last_name: {last_name}, student_number: {student_number}")

            if first_name and last_name and student_number:
                student_info.append({
                    "first_name": first_name,
                    "last_name": last_name,
                    "student_number": student_number,
                    "group_number": group_number
                })

    logger.info(f"RETURNING FROM extract_student_info_from_pdf: {student_info} {type(student_info)}")
    return student_info

def handle_uploaded_file(f, filepath):
    folder_path = os.path.dirname(filepath)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    with open(filepath, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def create_markscheme_objects(assignment, markscheme_data_frame):
    sections = []
    modules = []
    questions = []
    feedbacks = []
    
    current_section = None
    current_module = None
    current_question = None

    for index, row in markscheme_data_frame.iterrows():
        row_values = row.values.tolist()
        
        # Skip empty rows
        if all(pd.isna(value) for value in row_values):
            continue
            
        # Check first column for section/topic/question
        if pd.notna(row_values[0]):
            first_col = str(row_values[0]).strip()
            
            # Create Section
            if "Part" in first_col:
                current_section = Section.objects.create(
                    section_name=first_col,
                    assignment=assignment
                )
                sections.append(current_section)
                current_module = None  # Reset current module
                current_question = None  # Reset current question
                
            # Create Module (Topic)
            elif "Topic" in first_col:
                if current_section:
                    current_module = Module.objects.create(
                        module_name=first_col,
                        section=current_section
                    )
                    modules.append(current_module)
                    current_question = None  # Reset current question
                    
            # Create Question
            elif "Question" in first_col:
                if current_module:
                    current_question = Question.objects.create(
                        question=first_col,
                        module=current_module
                    )
                    questions.append(current_question)
        
        # Create Feedback
        if current_question and pd.notna(row_values[1]):
            try:
                feedback_key = str(row_values[1]).strip()
                feedback_text = str(row_values[2]).strip() if pd.notna(row_values[2]) else ""
                mark = float(row_values[3]) if pd.notna(row_values[3]) else 0.0
                
                feedback = Feedback.objects.create(
                    feedback_key=feedback_key,
                    feedback_text=feedback_text,
                    mark=mark,
                    question=current_question
                )
                feedbacks.append(feedback)
                
            except Exception as e:
                logger.error(f"Error creating feedback for question {current_question.question}: {str(e)}")
                logger.error(f"Row values: {row_values}")

    logger.info(f"\n=== Creation Summary ===")
    logger.info(f"Created {len(sections)} sections")
    logger.info(f"Created {len(modules)} modules")
    logger.info(f"Created {len(questions)} questions")
    logger.info(f"Created {len(feedbacks)} feedbacks")

    return sections, modules, questions, feedbacks

def handle_upload_excel_sheet(filePath, save_folder, filename, assignment):
    excel_file = pd.ExcelFile(filePath)
    sheet_names = excel_file.sheet_names
    df = pd.read_excel(filePath, sheet_name=sheet_names[0])

    csv_filename = os.path.join(save_folder, f"{filename}.csv")
    create_markscheme_objects(assignment, df)

    df.to_csv(csv_filename, index=False, encoding='cp1252')

    return sheet_names