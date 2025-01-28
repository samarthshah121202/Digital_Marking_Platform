import os
import pandas as pd
from django.conf import settings
from docx.shared import RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import fitz  # PyMuPDF
import re
import tabula
import logging
from docx import Document 
from pypdf import PdfReader
from openpyxl import load_workbook
from operator import attrgetter
from django.http import HttpResponse

from main.models import Feedback, Module, Question, Section
logger = logging.getLogger(__name__)

#def read_group_number(pdf_path):
    


def extract_student_info_from_pdf(pdf_path, is_group=False):
    # Use tabula to extract tables from the first page of the PDF
    reader = PdfReader(pdf_path)
    page = reader.pages[0]
    text = page.extract_text()
    txt_arr = text.split(" ")
    for i in range(len(txt_arr)):
        if txt_arr[i] == "\nGroup":
            group_num = txt_arr[i + 1]
    
    
    
    tables = tabula.read_pdf(pdf_path, pages=1, multiple_tables=True)
    #("group number: ", group_num)

    student_info = []

    if tables:
        # Assuming the first table is the one that contains the student data
        # You may need to inspect the tables to ensure this is correct
        table = tables[0]
      #  print(table)
        #logger.info(table)

        first_name = None
        last_name = None
        student_number = None
       # group_number = None 

        #logger.info(f"is_group: {is_group}")    

        # Assuming the table has columns for first name, last name, and student number
        if is_group:
            for index, row in table.iterrows():
               # print(index, row)
                
 
                
                logger.error(f"row: {row}")  

                last_name = row[0]
                first_name = row[1]
                student_number = row[2]
                #group_number = row[3]
                group_number = group_num
                #logger.info(f"first_name: {first_name}, last_name: {last_name}, student_number: {student_number}, group_number: {group_number}")
                student_info.append({
                    "first_name": first_name,
                    "last_name": last_name,
                    "student_number": student_number,
                    "group_number": group_number
                })
            #    print(student_info)
        else:
            for index, row in table.iterrows():
               # print(index, row)
                # Extract the first name, last name, and student number
                if row[0] == 'First Name':
                    first_name = row[1]
                elif row[0] == 'Last Name':
                    last_name = row[1]
                elif row[0] == 'Student ID':
                    student_number = row[1]
                #logger.info(f"first_name: {first_name}, last_name: {last_name}, student_number: {student_number}")

            if first_name and last_name and student_number:
                student_info.append({
                    "first_name": first_name,
                    "last_name": last_name,
                    "student_number": student_number,
                })

    #logger.info(f"RETURNING FROM extract_student_info_from_pdf: {student_info} {type(student_info)}")
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

    #logger.info(f"sections:{sections}")
    return sections

def handle_upload_excel_sheet(filePath, save_folder, filename, assignment) -> list[Section]:
    excel_file = pd.ExcelFile(filePath)
    sheet_names = excel_file.sheet_names
    df = pd.read_excel(filePath, sheet_name=sheet_names[0])

    csv_filename = os.path.join(save_folder,"markscheme",f"{filename}.csv")
    markscheme_obj = create_markscheme_objects(assignment, df)

    df.to_csv(csv_filename, index=False, encoding='cp1252')

    return markscheme_obj

def create_feedback_doc(student_infos, sections, assignment_title, student_feedback_doc_path, assignment, student_work):

    doc = Document()
    doc.add_heading(assignment_title, level=1)

    # Skip the header row [0] and get the student info from row [1]
    first_name = student_infos[1][0]  
    last_name = student_infos[1][1]   
    student_id = student_infos[1][2]  # Get the student ID from the third column
    
    # Create filename with student ID included
    if assignment.is_group_assignment:
        filename = f"Group_{student_work.group_number}_Student_Feedback.docx"
    else:
        filename = f"{first_name}_{last_name}_{student_id}_Student_Feedback.docx"
    full_path = os.path.join(student_feedback_doc_path, filename)

    # Create and populate student info table
    student_table = doc.add_table(rows=len(student_infos), cols=len(student_infos[0]))
    student_table.style = 'Table Grid'

    # Populate the table with data
    for row_idx, row_data in enumerate(student_infos):
        for col_idx, cell_data in enumerate(row_data):
            student_table.cell(row_idx, col_idx).text = str(cell_data)

    # Add sections, modules, and feedback
    for section in sections:
        doc.add_heading(section["section"].section_name, level=2)

        for module in section["modules"]:
            doc.add_heading(module["module"].module_name, level=4)

            for question in module["questions"]:
                feedback_paragraph = doc.add_paragraph()
                feedback_text = question["feedback_text"]
                
                # Add text with appropriate styling
                feedback_run = feedback_paragraph.add_run(feedback_text)
                feedback_run.font.color.rgb = RGBColor(0, 128, 0)  # Green color
                feedback_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    # Ensure directory exists and save
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    doc.save(full_path)
    #logger.info(f"Document saved successfully at: {full_path}")
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    response['Content-Disposition'] = 'attachment; filename="feedback.docx"'

    doc.save(response)

    return response

def add_to_feedback_sheet(workbook, id_table, group_table=None):

    def add_table(table, sheet_name, add_line=False):
      #  print(table)
        sheet = workbook[sheet_name]
        if add_line is True:
            table.append([" "])
        for row_data in table:
            new_row = sheet.max_row + 1
            for col_num, cell in enumerate(row_data, start=1):
                #logger.info(f"row={new_row} col={col_num} cell_data={cell} max_row={sheet.max_row}")
                sheet.cell(row=new_row, column=col_num).value = cell

    add_table(id_table, "Id List")
    
    # Only add group_table if it is provided (not None)
    if group_table is not None:
        add_table(group_table, "Group List", add_line=True)
    
    #add_to_marks_breakdown()
    return 
def question_mark_excel(workbook, processed_questions, processed_modules, processed_sections, group_number):
   # print("QUrkESTION MARK EXCEL CALED")
    marks_breakdown_sheet = workbook["Marks Breakdown"]

    marks = []  # {{ edit_3 }}
    print("group number is: ", group_number)
    
    for section in processed_sections:
        marks.append({section["total"]})  
        for module in section["modules"]:  
            marks.append({module["total"]})  

            for question in module["questions"]:  
                marks.append({question["mark"]}) 
    
    group_col = 1
    row_num = 1
    for col in marks_breakdown_sheet[row_num]:

        if col.value == "Group " + str(group_number):

            break
        else:
            group_col += 1

    list_of_list_marks = [[list(d)[0]] for d in marks]
    list_of_marks = [item[0] for item in list_of_list_marks]
    print("Marks:", list_of_marks) 

    for row_num, item in enumerate(list_of_marks, start=2):
       marks_breakdown_sheet.cell(row=row_num, column=group_col, value=item)


def question_mark_excel_student(workbook, processed_questions, processed_modules, processed_sections, student_number):
   # print("QUrkESTION MARK EXCEL CALED")
    marks_breakdown_sheet = workbook["Marks Breakdown"]

    marks = []  # {{ edit_3 }}
    print("student number is: ", student_number)
    
    for section in processed_sections:
        marks.append({section["total"]})  
        for module in section["modules"]:  
            marks.append({module["total"]})  

            for question in module["questions"]:  
                marks.append({question["mark"]}) 
    
    student_col = 1
    row_num = 1
    for col in marks_breakdown_sheet[row_num]:
        print(col.value)

        if col.value == student_number:

            break
        else:
            student_col += 1

    list_of_list_marks = [[list(d)[0]] for d in marks]
    list_of_marks = [item[0] for item in list_of_list_marks]
    print("Marks:", list_of_marks) 

    for row_num, item in enumerate(list_of_marks, start=2):
       marks_breakdown_sheet.cell(row=row_num, column=student_col, value=item)


""" def create_feedback_doc_download(student_infos, assignment_title, assignment, student_work):

    doc = Document()
    doc.add_heading(assignment_title, level=1)

    # Skip the header row [0] and get the student info from row [1]
    first_name = student_infos[1][0]  
    last_name = student_infos[1][1]   
    student_id = student_infos[1][2]  # Get the student ID from the third column
    
    # Create filename with student ID included
    if assignment.is_group_assignment:
        filename = f"Group_{student_work.group_number}_Student_Feedback.docx"
    else:
        filename = f"{first_name}_{last_name}_{student_id}_Student_Feedback.docx"
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    response['Content-Disposition'] = 'attachment; filename="feedback.docx"'

    doc.save(response)

    return response """
 
    

      

 

         
       
