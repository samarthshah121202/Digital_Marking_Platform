from django.shortcuts import render, redirect, get_object_or_404 # Importing the necessary functions
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Assignment, StudentWork, Section, StudentMark, Question, Feedback
import os
from .forms import AssignmentForm
from .utils import add_to_feedback_sheet, handle_uploaded_file, handle_upload_excel_sheet, extract_student_info_from_pdf, create_feedback_doc
from django.conf import settings
import csv
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Prefetch
import json
from django.db import transaction
from django.templatetags.static import static
from django.contrib import messages
from openpyxl import Workbook, load_workbook



logger = logging.getLogger(__name__)


def create_assignment(request): # Function to handle the creation of a new assignment
    if request.method == "POST": # Check if the request method is POST
        form = AssignmentForm(request.POST, request.FILES) # Create a form instance with the POST data and files
        logger.debug("Form data received: %s", form.data) # Log the form data
        logger.debug("Files received: %s", request.FILES) # Log the files

        if form.is_valid(): 
            try:
                # Get the project name and create a user-specific folder for the project
                project_name = form.cleaned_data["project_name"] # Get the project name from the form
                project_folder = os.path.join(settings.MEDIA_ROOT, "assignments", request.user.username, project_name) # Create a path to the project folder
                student_submissions_path = os.path.join(project_folder, "student_submissions")
                student_feedback_doc_path =  os.path.join(project_folder, "student_feedback")
                os.makedirs(student_submissions_path,exist_ok=True) # Create the project folder if it doesn't exist
                os.makedirs(student_feedback_doc_path,exist_ok=True)

                # Create an Assignment instance linked to the logged-in user
                assignment = Assignment.objects.create(
                    user=request.user, # Link the assignment to the logged-in user
                    project_name=project_name, # Set the project name
                    is_group_assignment=form.cleaned_data["is_group_assignment"]  # Store the group assignment status
                )

                # Save each student work file as a separate StudentWork instance
                for index, file in enumerate(request.FILES.getlist('student_work')): # Iterate over each uploaded student work file
                    # Save the student work file to the specific project folder
                    student_work_path = os.path.join(student_submissions_path, f"student_work_{index}.pdf") # Create a path to the student work file
                    handle_uploaded_file(file, student_work_path)

                    # Extract student information from the uploaded PDF using Tabula
                    student_info = extract_student_info_from_pdf(student_work_path, is_group=form.cleaned_data["is_group_assignment"])  # Extract student information from the uploaded PDF

                    logger.info(f"file: {file}") # Log the file

                    file_path = os.path.join( request.user.username, project_name, "student_submissions", f"student_work_{index}.pdf")

                    for student in student_info: # Iterate over each student in the student info list
                        # Optionally, save the extracted student info to the StudentWork model
                        student_work = StudentWork.objects.create( # Create a new StudentWork instance
                            student_file_path = file_path,
                            first_name=student['first_name'], # Set the first name
                            last_name=student['last_name'], # Set the last name
                            student_number=student['student_number'], # Set the student number
                            assignment=assignment, # Associate the student work with the created assignment
                            group_number=student['group_number']  # Associate the student work with the created assignment
                        )
                        # Add the student work instance to the assignment
                        assignment.student_files.add(student_work) # Add the student work instance to the assignment

                # Process the mark scheme Excel file if uploaded
                if 'markscheme' in request.FILES: # Check if the mark scheme file is uploaded
                    markscheme_path = os.path.join(project_folder, "markscheme","markscheme.xlsx")
                    handle_uploaded_file(request.FILES["markscheme"], markscheme_path)          
                    # Handle the uploaded Excel mark scheme (conversion to CSV or other processing)
                    handle_upload_excel_sheet(markscheme_path, project_folder, "markscheme", assignment)

                # Create and save the marks workbook
                wb = Workbook()
                
                sheet_names = ["Marks Breakdown","Id List", "Group List"] if assignment.is_group_assignment else ["Marks Breakdown","Id List"]
                for idx, name in enumerate(sheet_names):
                    wb.create_sheet(name, idx)
                
                wb.remove(wb.worksheets[-1])

                id_sheet = wb[sheet_names[1]]
                headers = ["Student Id", "Student Name", "Mark"]
                for col_num, header in enumerate(headers, start=1):
                    id_sheet.cell(row=1, column=col_num, value=header)

                group_list_sheet = wb[sheet_names[2]]
                headers = ["Student Id", "Student Name", "Mark"]
                for col_num, header in enumerate(headers, start=1):
                    group_list_sheet.cell(row=1, column=col_num, value=header)
                
                # Save the workbook in the project folder
                marks_file_path = os.path.join(project_folder, "student_marks.xlsx")
                wb.save(marks_file_path)

                # Save the assignment instance after creating student works and handling files
                assignment.save()

                logger.debug("Files uploaded and processed successfully!")
                return redirect('assignment_detail', assignment_id=assignment.id)  # Redirect to the dashboard or any appropriate page

            except Exception as e:
                logger.error("Error during file upload and processing: %s", str(e)) # Log the error
                return render(request, 'main/create_assignment.html', { # Render the create assignment template
                    'form': form, # Pass the form to the template
                    'error': f"Error uploading files: {str(e)}"
                })
        else:
            logger.error("Form validation errors: %s", form.errors) #
            return render(request, 'main/create_assignment.html', {
                'form': form,
                'error': "Form validation failed. Please check your inputs."
            })
    else:
        form = AssignmentForm()
    return render(request, 'main/create_assignment.html', {'form': form})


def homepage(request):
    return render(request, 'main/homepage.html')

def register(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        
        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            # Display an error message if the username is taken
            return render(request, 'main/register.html', {'error': 'Username already taken'})
        
        # Create a new user if the username is unique
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('dashboard')
    
    return render(request, 'main/register.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'main/login.html')

@login_required
def dashboard(request):
    # Filter assignments for the currently logged-in user
    assignments = Assignment.objects.filter(user=request.user)

    # Render the dashboard template with the assignments context
    return render(request, 'main/dashboard.html', {
        'assignments': assignments,
        'user': request.user,  # Optional, in case you want to greet the user or display the username
    })

@login_required
def assignment_detail(request, assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)
    student_info = StudentWork.objects.filter(assignment=assignment).values(
        'first_name',
        'last_name',
        'student_number',
        'group_number',
        'id',
        "is_marked"
    )


    context = {
        'assignment': assignment,
        'student_info': student_info
    }

    if assignment.is_group_assignment:
       return render(request, 'main/assignment_detail_group.html', context) 

    return render(request, 'main/assignment_detail_individual.html', context) 


@login_required
def delete_assignment(request, assignment_id):
    try:
        # Get the assignment and verify ownership
        assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)
        
        # Get the project folder path
        project_folder = os.path.join(settings.MEDIA_ROOT, "assignments", 
                                    request.user.username, assignment.project_name)
        
        # Delete all related database records
        assignment.delete()
        
        # Delete the project folder and all its contents
        if os.path.exists(project_folder):
            import shutil
            shutil.rmtree(project_folder)
        
        messages.success(request, 'Assignment deleted successfully')
        return redirect('dashboard')
    except Assignment.DoesNotExist:
        messages.error(request, 'Assignment not found')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f'Error deleting assignment: {str(e)}')
        return redirect('dashboard')


@login_required
def view_markscheme(request, assignment_id, submission_id):
    try:
        assignment = Assignment.objects.get(id=assignment_id)
        # Get the specific student work
        student_work = assignment.student_works.get(id=submission_id) if submission_id else assignment.student_works.first()
        
        path = student_work.student_file_path
        student_work_path = static(path)
        
        # Debug prints
        print(f"Student work path: {student_work_path}")
        
        sections = Section.objects.prefetch_related(
            'modules',
            'modules__questions',
            'modules__questions__feedbacks',
        ).filter(assignment=assignment)

        return render(request, 'main/view_markscheme.html', {
            'assignment': assignment,
            'sections': sections,
            'student_work': student_work,
            'student_work_path': student_work_path
        })
    except Assignment.DoesNotExist:
        return render(request, 'main/view_markscheme.html', {
            'error': 'Assignment not found'
        })

@login_required
@require_POST
def save_marks(request):

    def get_students(is_group_project, submission_id):
        if is_group_project:
            first_student_in_group = StudentWork.objects.get(id=submission_id)
            group_number = first_student_in_group.group_number
            return StudentWork.objects.filter(group_number=group_number)

        return StudentWork.objects.get(id=submission_id) 

    try:
        data = json.loads(request.body)
        marks_data = data.get('marks', {})
        submission_id= request.GET.get('submission_id', -1)
        is_group = int(request.GET.get("is_group", "0"))

        student = get_students(is_group == 1, submission_id)
        
       

        # Start a transaction to ensure all marks are saved or none are
        with transaction.atomic():
            for question_id, mark_info in marks_data.items():
                clean_question_id = question_id.replace('question-', '')
                # Get the question
                question = Question.objects.get(id=clean_question_id)
                
                # Get the feedback and create new mark
                feedback = Feedback.objects.get(id=mark_info['feedbackId'])

                if is_group == 0:
                    StudentMark.objects.create(
                        student=student,
                        question=question,
                        feedback=feedback
                    )
                    student.is_marked = True
                    student.save()
                else:
                    for participant in student:
                        StudentMark.objects.create(
                            student=participant,
                            question=question,
                            feedback=feedback
                        )
                        participant.is_marked = True
                        participant.save()


        return JsonResponse({
            'success': True,
            'message': 'All marks saved successfully'
        })
            
    except Question.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Question not found'
        }, status=404)
    except Feedback.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Feedback not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
def view_marks(request, assignment_id, submission_id):
    try:
        assignment = Assignment.objects.get(id=assignment_id)

        project_name = assignment.project_name # Get the project name from the form
        project_folder = os.path.join(settings.MEDIA_ROOT, "assignments", request.user.username, project_name) # Create a path to the project folder
        student_feedback_doc_path =  os.path.join(project_folder, "student_feedback")

        student_work = assignment.student_works.get(id=submission_id)

        if not isinstance(student_work, StudentWork):
            logger.error(f"Invalid student_work fetched: {student_work}")
        else:
            logger.info(f"Fetched StudentWork: {student_work} {student_work.first_name} {student_work.last_name}")

        sections = Section.objects.prefetch_related(
            'modules',
            'modules__questions',
            'modules__questions__feedbacks',
            'modules__questions__studentmark_set'
        ).filter(
            assignment=assignment,
            modules__questions__studentmark__student=student_work
        ).distinct()


        # Process the data to include marks
        processed_sections = []
        total_marks = 0

        for section in sections:
            section_total = 0
            processed_modules = []

            for module in section.modules.all():
                module_total = 0
                processed_questions = []
                
                for question in module.questions.all():
                    # Get the student's mark for this question
                    student_mark = question.studentmark_set.filter(student=student_work).first()
                    
                    question_data = {
                        'question': question,
                        'mark': student_mark.feedback.mark if student_mark else 0,
                        'feedback_text': student_mark.feedback.feedback_text if student_mark else "No mark recorded"
                    }
                    processed_questions.append(question_data)
                    if student_mark:
                        module_total += student_mark.feedback.mark
                
                module_data = {
                    'module': module,
                    'questions': processed_questions,
                    'total': module_total
                }

                processed_modules.append(module_data)
                section_total += module_total
            
            section_data = {
                'section': section,
                'modules': processed_modules,
                'total': section_total
            }
            # logger.info(f"section data {section_data}")
            processed_sections.append(section_data)
            total_marks += section_total

        # Modify the headers based on assignment type
        if assignment.is_group_assignment:
            student_info = [["First Name", "Last Name", "ID", "Group No."]]
            group_members = StudentWork.objects.filter(group_number=student_work.group_number, assignment=assignment).distinct()
            id_table = []
            group_table = []
            for member in group_members:
                student_info.append([
                    member.first_name, 
                    member.last_name, 
                    member.student_number,
                    member.group_number  # Add group number to each student's info
                ])
                id_table.append([member.student_number, member.first_name + " " + member.last_name, total_marks])
                group_table.append([member.student_number, member.first_name + " " + member.last_name, total_marks]) 

        else:
            student_info = [["First Name", "Last Name", "ID"]]
            tmp = StudentWork.objects.get(id=submission_id)
            student_info.append([tmp.first_name, tmp.last_name, tmp.student_number])
            id_table = [[tmp.student_number, tmp.first_name + " " + tmp.last_name, total_marks]]

        marks_file_path = os.path.join(project_folder, "student_marks.xlsx")
        wb = load_workbook(marks_file_path)

        create_feedback_doc(student_info,processed_sections, assignment.project_name, student_feedback_doc_path, assignment, student_work)
        add_to_feedback_sheet(wb, id_table, group_table)

        wb.save(marks_file_path)
        wb.close()

        return render(request, 'main/view_marks.html', {
            'assignment': assignment,
            'processed_sections': processed_sections,
            'total_marks': total_marks,
            'submission_id': student_work.id
        })
        
    except Assignment.DoesNotExist:
        return render(request, 'main/view_marks.html', {
            'error': 'Assignment not found'
        })
    
