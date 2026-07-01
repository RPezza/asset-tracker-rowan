from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Asset, Booking, UserMessage


class BookingDateValidationMixin:
    """Reusable booking validation logic for single and multi-asset forms."""

    @staticmethod
    def _validate_dates(start_date, end_date):
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")
        if start_date and start_date < timezone.now().date():
            raise forms.ValidationError("Start date cannot be in the past.")

    @staticmethod
    def _get_overlaps(asset, start_date, end_date, exclude_pk=None):
        overlaps = Booking.objects.filter(
            asset=asset,
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        if exclude_pk:
            overlaps = overlaps.exclude(pk=exclude_pk)
        return overlaps


class BookingForm(BookingDateValidationMixin, forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["asset", "start_date", "end_date", "purpose"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        asset = cleaned_data.get("asset")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        self._validate_dates(start_date, end_date)

        if asset and start_date and end_date:
            overlaps = self._get_overlaps(
                asset, start_date, end_date, exclude_pk=self.instance.pk
            )
            if overlaps.exists():
                booked = overlaps.first()
                raise forms.ValidationError(
                    f"{asset.name} is already booked between {booked.start_date} and {booked.end_date}."
                )

        return cleaned_data


class MultiAssetBookingForm(BookingDateValidationMixin, forms.Form):
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
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        self._validate_dates(start_date, end_date)

        if assets and start_date and end_date:
            conflicts = []
            for asset in assets:
                overlaps = self._get_overlaps(asset, start_date, end_date)
                if overlaps.exists():
                    booked = overlaps.first()
                    conflicts.append(
                        f"{asset.name} is already booked between {booked.start_date} and {booked.end_date}."
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
