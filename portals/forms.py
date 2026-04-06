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
        if school:
            self.fields['subjects'].queryset = Subject.objects.filter(school=school).order_by('category', 'name')
            self.fields['class_arms'].queryset = ClassArm.objects.filter(school=school).order_by('class_level__order', 'name')

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
        super().__init__(*args, **kwargs)


        



