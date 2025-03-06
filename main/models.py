from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Max, Sum

class Assignment(models.Model):
    # The user who created the assignment
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    project_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_group_assignment = models.BooleanField(default=False)

    # Updated related_name for the ManyToMany relationship to avoid clash with student_works
    student_files = models.ManyToManyField('StudentWork', related_name='related_assignments')

    @property
    def total_possible_marks(self):
        """Calculate total possible marks for the entire assignment"""
        sections = Section.objects.filter(
            modules__questions__feedbacks__isnull=False
        ).filter(assignment=self).distinct()
        return sum(section.total_possible_marks for section in sections)

    def __str__(self):
        return self.project_name


class StudentWork(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='student_works'
    )
    student_file_path = models.CharField(max_length=1000)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    student_number = models.CharField(max_length=20, blank=True, null=True)
    group_number = models.SmallIntegerField(null=True, blank=True)
    is_marked = models.BooleanField(default=False)


# read the markscheme file and create the questions and feedbacks
class Section(models.Model):
    section_name = models.CharField(max_length=200)
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE,
        related_name='sections'
    )

    @property
    def total_possible_marks(self):
        """Calculate total possible marks for this section"""
        return sum(module.total_possible_marks for module in self.modules.all())

    def __str__(self):
        return self.section_name

class Module(models.Model):
    module_name = models.CharField(max_length=200)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='modules')

    @property
    def total_possible_marks(self):
        """Calculate total possible marks for this module"""
        return sum(question.total_possible_marks for question in self.questions.all())

    def __str__(self):
        return self.module_name

class Question(models.Model):
    question = models.CharField(max_length=500)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='questions')

    @property
    def total_possible_marks(self):
        """Get the highest possible mark for this question"""
        max_mark = self.feedbacks.aggregate(max_mark=Max('mark'))['max_mark']
        return max_mark if max_mark is not None else 0

    def get_current_mark(self, student):
        """Get the current mark for a specific student"""
        student_mark = self.studentmark_set.filter(student=student).first()
        return student_mark.feedback.mark if student_mark else 0

    def __str__(self):
        return self.question

class Feedback(models.Model):
    feedback_key = models.CharField(max_length=200)
    feedback_text = models.TextField()
    mark = models.FloatField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='feedbacks')

    def __str__(self):
        return f"{self.feedback_key} - {self.mark} marks"

class StudentMark(models.Model):
    student = models.ForeignKey(StudentWork, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, null=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    custom_feedback = models.TextField(blank=True, null=True)
    custom_mark = models.FloatField(blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'question', 'feedback']

    def __str__(self):
        return f"{self.student.username} - {self.question.question} - {self.feedback.mark} marks"






