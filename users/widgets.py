from django import forms


class DexoraImageInput(forms.ClearableFileInput):
    template_name = "users/widgets/image_input.html"
