from django import forms

class RatingForm(forms.Form):
    score = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 11)],
        label="Nota (1 a 10)"
    )

