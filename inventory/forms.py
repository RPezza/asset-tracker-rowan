from django import forms
from django.utils import timezone

from .models import Asset, Booking, UserMessage

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["asset", "start_date", "end_date", "purpose"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset"].queryset = Asset.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        asset = cleaned_data.get("asset")
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end and start > end:
            raise forms.ValidationError("End date must be after start date.")
        if start and start < timezone.now().date():
            raise forms.ValidationError("Start date cannot be in the past.")

        if asset and start and end:
            overlapping = Booking.objects.filter(
                asset=asset,
                start_date__lte=end,
                end_date__gte=start,
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                first = overlapping.first()
                raise forms.ValidationError(
                    f"{asset.name} is already booked between {first.start_date} and {first.end_date}."
                )
        return cleaned_data


class ContactForm(forms.ModelForm):
    class Meta:
        model = UserMessage
        fields = ["name", "email", "subject", "message"]


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["name", "description", "category", "available"]
