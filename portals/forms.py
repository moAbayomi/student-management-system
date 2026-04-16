from django import forms
from users.models import User
from academics.models import Subject, ClassArm
import random
import string


def generate_temp_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


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


