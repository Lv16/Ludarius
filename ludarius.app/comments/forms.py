from django import forms


class CommentForm(forms.Form):
    text = forms.CharField(
        min_length=3,
        max_length=500,
        required=True,
        strip=True,
        label="Comentário"
    )
