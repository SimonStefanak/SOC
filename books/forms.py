from django import forms

from .models import UserBook


class ShelfForm(forms.ModelForm):
    """The controls on the book card: shelf status, dates, rating and heart.
    Saved instantly (in the background) whenever one of them changes."""

    class Meta:
        model = UserBook
        fields = ["status", "date_started", "date_finished", "rating", "favorite"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # "Add to shelf" (empty) is allowed: the view decides what it means.
        self.fields["status"].required = False

    def clean(self):
        cleaned = super().clean()
        started, finished = cleaned.get("date_started"), cleaned.get("date_finished")
        if started and finished and finished < started:
            self.add_error("date_finished", "The finish date can't be before the start date.")
        return cleaned


class ReviewForm(ShelfForm):
    """Everything on the card plus the review text: used by the "Save review" button."""

    class Meta(ShelfForm.Meta):
        fields = ShelfForm.Meta.fields + ["review_text"]

    def clean_review_text(self):
        return (self.cleaned_data.get("review_text") or "").strip()
