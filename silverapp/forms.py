from django import forms
from .models import *

class loginForm(forms.ModelForm):
    class Meta:
        model=login_tbl
        fields='__all__'
class passForm(forms.ModelForm):
    class Meta:
        model=login_tbl
        fields=['password']


class addsubuserForm(forms.ModelForm):
    username = forms.CharField(required=False, label="Username")
    password = forms.CharField(widget=forms.PasswordInput, required=False, label="New password")

    class Meta:
        model = add_subuser
        fields = ['username', 'password']  # only include fields you want editable

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            # If empty, keep the existing FK
            return self.instance.username

        try:
            return login_tbl.objects.get(username=username)
        except login_tbl.DoesNotExist:
            raise forms.ValidationError("Entered username does not exist in the system.")
class editsubuserForm(forms.ModelForm):
    class Meta:
        model=add_subuser
        fields='__all__'
class viewsubuserForm(forms.ModelForm):
    class Meta:
        model=add_subuser
        fields='__all__'
class SubMasterForm(forms.ModelForm):
    class Meta:
        model = SubMaster
        fields = '__all__'
        
        widgets = {
            'password': forms.PasswordInput(render_value=True),
        }
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'account', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class MotorRatingForm(forms.ModelForm):
    class Meta:
        model = MotorRating
        fields = ['kw', 'hp', 'account', 'status']
        widgets = {
            'kw': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'i.e. 0.50, 0.75, 1.00'}),
            'hp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'i.e. 0.50, 0.75, 1.00'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class PhaseForm(forms.ModelForm):
    class Meta:
        model = Phase
        fields = ['name', 'short_name', 'account', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class HertzForm(forms.ModelForm):
    class Meta:
        model = Hertz
        fields = ['hz_name', 'account', 'is_active']
        widgets = {
            'hz_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'i.e. 50 Hz, 60 Hz'}),
            'account': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RPMForm(forms.ModelForm):
    class Meta:
        model = RPM
        fields = ['rpm_name', 'account', 'is_active']
        widgets = {
            'rpm_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2800, 1440'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }