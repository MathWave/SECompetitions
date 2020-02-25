from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={"class": "input_simple"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input_simple"}))


class FileForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'input_simple'}))


class NewCompetitionForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput())


class NewTaskForm(forms.Form):
    name = forms.CharField()


class TestsForm(forms.Form):
    tests = forms.FileField(widget=forms.FileInput())


class SamplesForm(forms.Form):
    samples = forms.FileField(widget=forms.FileInput())