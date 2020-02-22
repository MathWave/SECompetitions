from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={"class": "input_simple"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input_simple"}))


class FileForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'input_simple'}))
