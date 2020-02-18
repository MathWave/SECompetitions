from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={"class":"input_simple"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class":"input_simple"}))
