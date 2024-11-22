from django import forms
from .models import Product, Feedback
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class SignupForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password', max_length=128)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password', max_length=128)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        if password1 and len(password1) < 8:  
            raise ValidationError("Password must be at least 8 characters long.")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")



class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description']

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['customer_name', 'email', 'message', 'rating']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 10}),
        }
