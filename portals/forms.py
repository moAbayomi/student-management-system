from django import forms
from django.db import transaction
from django.forms import inlineformset_factory
from users.models import User
from profiles.models import TeacherProfile
from academics.models import Subject, ClassArm, SubjectAssignment
import random
import string


def generate_temp_password():
    """ return ''.join(random.choices(string.ascii_letters + string.digits, k=10)) """
    return 'pswdtakbir1234'


class TeacherCreationForm(forms.Form):
    first_name   = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all',
        'placeholder': 'First name'
    }))
    last_name    = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all',
        'placeholder': 'Last name'
    }))
    username     = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all',
        'placeholder': 'Username'
    }))
    email        = forms.EmailField(required=False, widget=forms.EmailInput(attrs={
        'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all',
        'placeholder': 'Email (optional)'
    }))
    employee_id  = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all',
        'placeholder': 'e.g. TCH001'
    }))
    subjects     = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )
    class_arms   = forms.ModelMultipleChoiceField(
        queryset=ClassArm.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    def __init__(self, school=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subjects'].queryset = Subject.objects.all().order_by('name')
        self.fields['class_arms'].queryset = ClassArm.objects.all().order_by('class_level__order', 'name')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
    

class StudentCreationForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all',
        'placeholder': 'First name'
    }))

    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all',
        'placeholder': 'Last name'
    }))

    username     = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all',
        'placeholder': 'Username'
    }))
    email        = forms.EmailField(required=False, widget=forms.EmailInput(attrs={
        'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all',
        'placeholder': 'Email (optional)'
    }))

    class_arm = forms.ModelChoiceField(
        queryset=ClassArm.objects.none(),
        required=False, # Important: False because Teachers won't see/fill it
        label="Select Class Arm",
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-400 focus:bg-white transition-all',
        'placeholder': 'Choose class arm'})
    )

    date_of_birth = forms.DateField(
    required=True, 
    widget=forms.DateInput(
        format='%Y-%m-%d',
        attrs={
        'type': 'date',           
        'class': 'form-input',     
        'max': '2026-04-04',       
    }))

    def __init__(self, *args, **kwargs):
        user_role = kwargs.pop('user_role', None)
        super().__init__(*args, **kwargs)

        if user_role == 'ADMIN':
            self.fields['class_arm'].queryset = ClassArm.objects.all()
            self.fields['class_arm'].required = True

        else:
            self.fields['class_arm'].widget = forms.HiddenInput()


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
    

class UserIdentityForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class TeacherWorkInfoForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ['date_joined']
    

