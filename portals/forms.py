from django import forms
from django.db import transaction
from django.forms import inlineformset_factory
from django.core.validators import EmailValidator
from users.models import User
from profiles.models import TeacherProfile, TeacherRole
from academics.models import Subject, Class, ClassArm, SubjectAssignment
import random
import string


def generate_temp_password():
    """ return ''.join(random.choices(string.ascii_letters + string.digits, k=10)) """
    return 'pswdtakbir1234'

class TeacherCreationForm(forms.Form):

    # ── Biographical Info ──
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    middle_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True, validators=[EmailValidator()])
    phone = forms.CharField(max_length=20, required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')], required=True)
    dob = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    address = forms.CharField(widget=forms.Textarea, required=False)
    religion = forms.CharField(required=False)
    state_of_origin = forms.CharField(required=False)

    photo = forms.ImageField(required=False)

    # ── Professional Profiles ──
    qualification = forms.ChoiceField(
        choices=[
            ('B.Ed', 'B.Ed'), ('B.Sc', 'B.Sc'), ('B.A', 'B.A'),
            ('B.Tech', 'B.Tech'), ('M.Sc', 'M.Sc'), ('M.A', 'M.A'),
            ('M.Ed', 'M.Ed'), ('PGDE', 'PGDE'), ('Ph.D', 'Ph.D'),
            ('NCE', 'NCE'), ('Other', 'Other')
        ],
        required=True
    )
    years_of_exp = forms.IntegerField(min_value=0, max_value=50, required=False)
    
    # ── Institutional Scoping ──
    department = forms.ChoiceField(
        choices=TeacherProfile.Department.choices,
        required=True,
        label="Primary Department"
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'flex flex-wrap gap-1.5'})
    )
    max_weekly_hours = forms.IntegerField(min_value=1, max_value=40, initial=30, required=False)
    
    save_mode = forms.CharField(widget=forms.HiddenInput(), initial='complete')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subjects'].queryset = Subject.objects.all()


class StudentCreationForm(forms.Form):
    first_name = forms.CharField(max_length=50, required=True)
    middle_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=True)
    dob = forms.DateField(required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')], required=True)
    state_of_origin = forms.CharField(required=False)
    religion = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)

    # Step 2: Academic
    admission_type = forms.CharField(initial='New Admission')
    entry_term = forms.CharField(initial='2nd Term 2026')
    fee_plan = forms.CharField(initial='Full Payment')
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
    


class ClassArmForm(forms.Form):
    class_arm = forms.ModelChoiceField(
        queryset=ClassArm.objects.none(),
        required=False,
        label="Select Class Arm",
        empty_label="Choose Class Arm",
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_arm'].queryset = ClassArm.objects.select_related('class_level').all()



class SubjectEnrollmentForm(forms.Form):
    subjects = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Subject.objects.none(),
        widget= forms.CheckboxSelectMultiple()
    )

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        target_categories = kwargs.pop('target_categories')
        super().__init__(*args, **kwargs)

        self.fields['subjects'].queryset = Subject.objects.filter(category__in=target_categories).order_by('category', 'name')

        core_ids = Subject.objects.filter(category__icontains='CORE').values_list('id', flat=True)
        self.core_ids = list(core_ids)

        if student:
            current_ids = list(student.subjects.values_list('id', flat=True))
            # Merge both lists so nothing is missed
            self.fields['subjects'].initial = list(set(self.core_ids + current_ids))
        else:
            # If it's a brand new student, just check the Core ones
            self.fields['subjects'].initial = self.core_ids


class SubjectAssignmentForm(forms.ModelForm):
    all_arms = forms.BooleanField(required=False, label='assign to all arms')

    class Meta:
        model = SubjectAssignment
        fields = ['subject', 'class_arm', 'session', 'all_arms']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'class_arm': forms.Select(attrs={'class': 'form-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
        }
    
SubjectAssignmentFormSet = inlineformset_factory(
    TeacherProfile,
    SubjectAssignment,
    form=SubjectAssignmentForm,
    extra=3,
    can_delete=True,
)
    
class ChangeClassTeacher(forms.Form):
    classes = forms.ModelMultipleChoiceField(
        required=False,
        queryset=ClassArm.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2'
        }),
        label="Assigned Class Arms"
    )

    def __init__(self, *args, **kwargs):
        self.teacher_profile = kwargs.pop('teacher_profile', None)
        super().__init__(*args, **kwargs)

        if self.teacher_profile:
            self.fields['classes'].initial = ClassArm.objects.filter(class_teacher=self.teacher_profile)

    def save(self):
        selected_classes = self.cleaned_data.get('classes')
        teacher_user = self.teacher_profile 

        with transaction.atomic():
            ClassArm.objects.filter(class_teacher=teacher_user).update(class_teacher=None)

            if selected_classes:
                for arm in selected_classes:
                    arm.class_teacher = teacher_user
                    arm.save()
                    
        return selected_classes
    


