from django import forms
from .models import User

class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    master_password = forms.CharField(widget=forms.PasswordInput, required=True, label="Master Password")
    master_password_confirm = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm Master Password")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_master_password_confirm(self):
        master_password = self.cleaned_data.get("master_password")
        master_password_confirm = self.cleaned_data.get("master_password_confirm")

        if master_password != master_password_confirm:
            raise forms.ValidationError("The two master password fields didn't match.")
        return master_password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["master_password"])
        if commit:
            user.save()
        
        user.set_master_key_material(self.cleaned_data["master_password"])
        return user



class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "contact_number", "photo"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email