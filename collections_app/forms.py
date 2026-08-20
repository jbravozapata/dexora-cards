from django import forms
from .models import UserCollectionItem


class CollectionItemForm(forms.ModelForm):
    class Meta:
        model = UserCollectionItem
        fields = ["quantity", "variant", "condition", "notes"]
        widgets = {"quantity": forms.NumberInput(attrs={"min": 1, "max": 999}), "notes": forms.Textarea(attrs={"rows": 3})}
