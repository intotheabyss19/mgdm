# academics/forms.py

from django import forms
from .models import Result

class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['obtained_marks']

    def clean_obtained_marks(self):
        marks = self.cleaned_data.get('obtained_marks')

        max_marks = self.instance.test.max_marks

        if marks < 0 or marks > max_marks:
            raise forms.ValidationError(f"Marks must be between 0 and {max_marks}.")

        return marks
