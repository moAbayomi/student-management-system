from django import forms
from django.core.validators import EmailValidator
from django.forms import modelformset_factory

from academics.models import GradeComponent, Subject
from profiles.models import TeacherProfile, TeacherRole
from schools.models import School
from users.models import User


class TeacherCreationForm(forms.Form):
    # ── Biographical Info ──
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    middle_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True, validators=[EmailValidator()])
    phone = forms.CharField(max_length=20, required=True)
    gender = forms.ChoiceField(choices=[("M", "Male"), ("F", "Female")], required=True)
    dob = forms.DateField(required=True, widget=forms.DateInput(attrs={"type": "date"}))
    address = forms.CharField(widget=forms.Textarea, required=False)
    religion = forms.CharField(required=False)
    state_of_origin = forms.CharField(required=False)

    photo = forms.ImageField(required=False)

    # ── Professional Profiles ──
    qualification = forms.ChoiceField(
        choices=[
            ("B.Ed", "B.Ed"),
            ("B.Sc", "B.Sc"),
            ("B.A", "B.A"),
            ("B.Tech", "B.Tech"),
            ("M.Sc", "M.Sc"),
            ("M.A", "M.A"),
            ("M.Ed", "M.Ed"),
            ("PGDE", "PGDE"),
            ("Ph.D", "Ph.D"),
            ("NCE", "NCE"),
            ("Other", "Other"),
        ],
        required=True,
    )
    years_of_exp = forms.IntegerField(min_value=0, max_value=50, required=False)

    # ── Institutional Scoping ──
    department = forms.ChoiceField(
        choices=TeacherProfile.Department.choices,
        required=True,
        label="Primary Department",
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "flex flex-wrap gap-1.5"}),
    )
    max_weekly_hours = forms.IntegerField(
        min_value=1, max_value=40, initial=30, required=False
    )

    save_mode = forms.CharField(widget=forms.HiddenInput(), initial="complete")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subjects"].queryset = Subject.objects.all()


class StudentCreationForm(forms.Form):
    first_name = forms.CharField(max_length=50, required=True)
    middle_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=True)
    dob = forms.DateField(required=True)
    gender = forms.ChoiceField(choices=[("M", "Male"), ("F", "Female")], required=True)
    state_of_origin = forms.CharField(required=False)
    religion = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)

    # Step 2: Academic
    admission_type = forms.CharField(initial="New Admission")
    entry_term = forms.CharField(initial="2nd Term 2026")
    fee_plan = forms.CharField(initial="Full Payment")
    previous_school = forms.CharField(max_length=255, required=False)
    previous_class = forms.CharField(max_length=50, required=False)

    # Step 3: Guardian
    guardian_first_name = forms.CharField(required=False)
    guardian_last_name = forms.CharField(required=False)
    guardian_relationship = forms.CharField(required=False)
    guardian_phone = forms.CharField(required=False)
    guardian_email = forms.EmailField(required=False)
    guardian_occupation = forms.CharField(max_length=100, required=False)
    guardian_nin = forms.CharField(max_length=50, required=False)
    guardian_address = forms.CharField(widget=forms.Textarea, required=False)

    emergency_name = forms.CharField(max_length=200, required=False)

    # Step 4: Medical / Notes
    blood_group = forms.CharField(required=False)
    genotype = forms.CharField(required=False)
    emergency_phone = forms.CharField(max_length=20, required=False)
    allergies = forms.CharField(widget=forms.Textarea, required=False)
    medical_conditions = forms.CharField(widget=forms.Textarea, required=False)
    disability = forms.CharField(required=False)
    admin_notes = forms.CharField(widget=forms.Textarea, required=False)

    def clean(self):
        """
        Production Custom Validation Hook
        """
        cleaned_data = super().clean()
        # You can add conditional checks here if save_mode == 'complete'
        return cleaned_data


class NewArm(forms.Form):
    name = forms.CharField(label="input arm name", max_length=10, required=True)


class AssignClassTeacher(forms.Form):
    teacher = forms.ModelChoiceField(
        required=True, queryset=TeacherProfile.objects.all()
    )


class CoreSubjects(forms.Form):
    core_subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={"class": "hidden", "x-ref": "coreSubjectsSelect"}
        ),
    )


class SchoolSettingsForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            # Identity
            "name",
            "slug",
            "tagline",
            "about",
            # Branding
            "logo",
            "favicon",
            "hero_image",
            "primary_color",
            "secondary_color",
            # Contact
            "address",
            "phone",
            "email",
            "website",
            # Leadership
            "principal_name",
            "principal_message",
            "principal_photo",
            # Preferences
            "pass_mark",
            "grading_system",
            "timezone",
        ]
        widgets = {
            "about": forms.Textarea(attrs={"rows": 3}),
            "address": forms.Textarea(attrs={"rows": 2}),
            "principal_message": forms.Textarea(attrs={"rows": 3}),
            "pass_mark": forms.NumberInput(attrs={"step": "0.01", "min": 0}),
        }


class GradeComponentForm(forms.ModelForm):
    class Meta:
        model = GradeComponent
        fields = ["name", "max_score", "is_exam"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. CA1, Exam"}),
            "max_score": forms.NumberInput(attrs={"step": "0.01", "min": 0}),
        }


class BaseGradeComponentFormSet(forms.BaseModelFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        total = 0.0
        seen_names = set()

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            name = (form.cleaned_data.get("name") or "").strip().lower()
            score = form.cleaned_data.get("max_score") or 0

            if name in seen_names:
                form.add_error("name", f'"{name}" is already used above.')
            elif name:
                seen_names.add(name)

            total += score

        if not seen_names:
            raise forms.ValidationError("Add at least one grade component.")

        if abs(total - 100) > 0.001:  # tolerate float rounding
            raise forms.ValidationError(
                f"Grade components must add up to 100. Currently: {total:g}."
            )


GradeComponentFormSet = modelformset_factory(
    GradeComponent,
    form=GradeComponentForm,
    formset=BaseGradeComponentFormSet,
    extra=1,
    can_delete=True,
)
