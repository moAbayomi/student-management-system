from django import forms
from django.contrib.auth import get_user_model

from .models import AcademicSession, AcademicTerm

User = get_user_model()


class StaffCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-input"})
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "phone_number",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit role choices so a Principal can't accidentally create a 'STUDENT' here
        self.fields["role"].choices = [
            ("ADMIN", "Admin/Bursar"),
            ("TEACHER", "Teacher"),
        ]


class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ["name", "start_year", "end_year", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        sy, ey = cleaned.get("start_year"), cleaned.get("end_year")
        if sy and ey and ey <= sy:
            self.add_error("end_year", "End year must be after start year.")

        sd, ed = cleaned.get("start_date"), cleaned.get("end_date")
        if sd and ed and ed <= sd:
            self.add_error("end_date", "End date must be after start date.")

        return cleaned


class AcademicTermForm(forms.ModelForm):
    class Meta:
        model = AcademicTerm
        fields = ["start_date", "end_date", "grading_deadline", "next_term_begins"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "next_term_begins": forms.DateInput(attrs={"type": "date"}),
            "grading_deadline": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Required so the datetime-local input renders correctly on GET
        self.fields["grading_deadline"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")

        if start and end and end <= start:
            self.add_error("end_date", "End date must be after start date.")

        deadline = cleaned.get("grading_deadline")
        if deadline and end and deadline.date() > end:
            self.add_error(
                "grading_deadline",
                "Grading deadline should not be after the term ends.",
            )
        return cleaned
