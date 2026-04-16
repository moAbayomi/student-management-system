from django import forms
from .models import Class, ClassArm, Subject
from users.models import User

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'order'] # We exclude 'school' because the Admin sets it automatically
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-3 rounded-lg border border-slate-200', 'placeholder': 'e.g. JSS 1'}),
            'order': forms.NumberInput(attrs={'class': 'w-full p-3 rounded-lg border border-slate-200'}),
        }

class ClassArmForm(forms.ModelForm):
    class Meta:
        model = ClassArm
        fields = [ 'name', 'class_teacher']
        labels = {
            'class_level': 'Select Grade/Level',
            'name': 'Arm Name (e.g., A, B, or Gold)',
            'class_teacher': 'Assign a Form Teacher (Optional)',
        }
        widgets = {
            'class_level': forms.Select(attrs={'class': 'w-full p-3 rounded-lg border border-slate-200'}),
            'name': forms.TextInput(attrs={'class': 'w-full p-3 rounded-lg border border-slate-200', 'placeholder': 'e.g. A or Gold'}),
            'class_teacher': forms.Select(attrs={'class': 'w-full p-3 rounded-lg border border-slate-200'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_teacher'].queryset = User.objects.filter(role='TEACHER')


