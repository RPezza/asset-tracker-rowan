from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
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


class MultiAssetBookingForm(forms.Form):
    assets = forms.ModelMultipleChoiceField(
        queryset=Asset.objects.none(),
        required=True,
        widget=forms.SelectMultiple,
    )
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    purpose = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assets"].queryset = Asset.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        assets = cleaned_data.get("assets")
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end and start > end:
            raise forms.ValidationError("End date must be after start date.")
        if start and start < timezone.now().date():
            raise forms.ValidationError("Start date cannot be in the past.")

        if assets and start and end:
            conflicts = []
            for asset in assets:
                overlapping = Booking.objects.filter(
                    asset=asset,
                    start_date__lte=end,
                    end_date__gte=start,
                )
                if overlapping.exists():
                    first = overlapping.first()
                    conflicts.append(
                        f"{asset.name} is already booked between {first.start_date} and {first.end_date}."
                    )

            if conflicts:
                raise forms.ValidationError(conflicts)

        return cleaned_data


class ContactForm(forms.ModelForm):
    class Meta:
        model = UserMessage
        fields = ["name", "email", "subject", "message"]


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["name", "description", "category", "available"]


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        if commit:
            user.save()
        return user
