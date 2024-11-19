from .models import Assignment, StudentWork 

def assignment_detail(request, assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)
    student_info = StudentWork.objects.filter(assignment=assignment).values(
        'student__first_name',
        'student__last_name',
        'student__student_number',
        'group_number',
        'id as submission_id'
    )
    context = {
        'assignment': assignment,
        'student_info': student_info
    }
    return render(request, 'main/assignment_detail.html', context) 