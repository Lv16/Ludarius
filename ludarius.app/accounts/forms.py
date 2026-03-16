from django import forms

from .models import AvailabilityAlert, Collection, MediaStatus, Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio"]


class MediaStatusForm(forms.Form):
    status = forms.ChoiceField(choices=MediaStatus.Status.choices, label="Status")


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["title", "description", "is_public"]


class CollectionAddItemForm(forms.Form):
    collection = forms.ModelChoiceField(queryset=Collection.objects.none(), label="Colecao")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["collection"].queryset = Collection.objects.filter(user=user).order_by("-created_at")


class AvailabilityAlertForm(forms.ModelForm):
    class Meta:
        model = AvailabilityAlert
        fields = []
