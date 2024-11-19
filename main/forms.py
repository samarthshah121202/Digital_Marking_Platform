from django import forms

# Custom widget to allow multiple file selection
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True  # Enables selecting multiple files in the file input

# Custom field to handle multiple file uploads
class MultipleFileField(forms.FileField):
    """
    A custom file field that allows multiple files to be uploaded.
    This uses MultipleFileInput as the widget.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        """
        Override the clean method to process multiple files individually
        and validate each one using the parent FileField's clean method.
        """
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            # Clean each file in the list if multiple files are provided
            result = [single_file_clean(d, initial) for d in data]
        else:
            # Otherwise, process it as a single file and wrap it in a list
            result = [single_file_clean(data, initial)]
        return result

# Basic form for testing or other uses
class SimpleForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)

# Assignment Form
class AssignmentForm(forms.Form):
    project_name = forms.CharField(label="Project Name", max_length=100)
    student_work = MultipleFileField(
        label="Student Work (PDFs)", 
        required=True,
        help_text="Upload multiple PDF files for each student's work"
    )
    is_group_assignment = forms.BooleanField(
        label="Is this a group assignment?",
        required=False
    )
    markscheme = forms.FileField(
        label="Mark Scheme (Excel)", 
        required=False, 
        help_text="Upload an Excel file for the mark scheme"
    )

    def clean_project_name(self):
        # Custom validation for project_name if needed
        project_name = self.cleaned_data.get("project_name")
        if not project_name:
            raise forms.ValidationError("Project name is required.")
        return project_name
