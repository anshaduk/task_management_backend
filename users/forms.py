

from django import forms
from .models import CustomUser

class UserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        
        if role == 'superadmin':
            self.instance.is_staff = True
            self.instance.is_superuser = True
        elif role == 'admin':
            self.instance.is_staff = True
            self.instance.is_superuser = False
        else:
            self.instance.is_staff = False
            self.instance.is_superuser = False

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  
        if commit:
            user.save()
        return user
