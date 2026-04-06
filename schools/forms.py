from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class StaffCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit role choices so a Principal can't accidentally create a 'STUDENT' here
        self.fields['role'].choices = [
            ('ADMIN', 'Admin/Bursar'),
            ('TEACHER', 'Teacher'),
        ]