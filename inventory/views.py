from datetime import date, timedelta
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AssetForm, BookingForm, ContactForm, MultiAssetBookingForm, RegisterForm
from .models import Asset, Booking, UserMessage


def _annotate_next_available(assets):
    today = date.today()

    for asset in assets:
        # Determine whether the asset is booked today and when it becomes available.
        is_today_booked = Booking.objects.filter(
            asset=asset,
            start_date__lte=today,
            end_date__gte=today,
        ).exists()

        if is_today_booked:
            latest_booking = Booking.objects.filter(
                asset=asset,
                end_date__gte=today,
            ).order_by("end_date").last()
            asset.next_available = latest_booking.end_date + timedelta(days=1)
            asset.available = False
        else:
            asset.next_available = today
            asset.available = True
    return assets


def _group_bookings(bookings, user_id):
    grouped = {}

    for booking in bookings:
        group_key = booking.booking_group or f"legacy-{booking.pk}"
        if group_key not in grouped:
            grouped[group_key] = {
                "id": booking.id,
                "assets": [booking.asset.name],
                "start_date": booking.start_date,
                "end_date": booking.end_date,
                "user": booking.user,
                "can_edit": booking.user_id == user_id or booking.user.is_staff,
            }
        else:
            grouped[group_key]["assets"].append(booking.asset.name)

    grouped_bookings = []
    for group in grouped.values():
        group["asset_count"] = len(group["assets"])
        group["assets_display"] = ", ".join(group["assets"])
        grouped_bookings.append(group)

    return grouped_bookings


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect("home")
        messages.error(request, "Invalid username or password.")
    return render(request, "inventory/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid(): 
            form.save()
            messages.success(request, "Account created. You can now log in.")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "inventory/register.html", {"form": form})


@login_required(login_url="login")
def home(request):
    assets = _annotate_next_available(Asset.objects.all())
    return render(request, "inventory/home.html", {"assets": assets})



@login_required
def asset_list(request):
    assets = _annotate_next_available(Asset.objects.all())
    return render(request, "inventory/asset_list.html", {"assets": assets})


@login_required
def book_asset(request):
    assets = _annotate_next_available(Asset.objects.all())
    if request.method == "POST":
        form = MultiAssetBookingForm(request.POST)
        if form.is_valid():
            selected_assets = form.cleaned_data["assets"]
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
            purpose = form.cleaned_data["purpose"]
            booking_group = str(uuid.uuid4())

            for asset in selected_assets:
                Booking.objects.create(
                    user=request.user,
                    asset=asset,
                    booking_group=booking_group,
                    start_date=start_date,
                    end_date=end_date,
                    purpose=purpose,
                )

            messages.success(request, f"Booked {selected_assets.count()} asset(s) successfully.")
            return redirect("asset_list")
    else:
        form = MultiAssetBookingForm()

    selected_asset_ids = [str(asset_id) for asset_id in (form["assets"].value() or [])]
    return render(
        request,
        "inventory/book_asset.html",
        {"form": form, "assets": assets, "selected_asset_ids": selected_asset_ids},
    )

@login_required
def booking_list(request):
    view_filter = request.GET.get("view", "all")
    bookings = Booking.objects.select_related("asset", "user").order_by("-start_date", "-end_date", "id")

    if view_filter == "Your Bookings":
        bookings = bookings.filter(user=request.user)

    grouped_bookings = _group_bookings(bookings, request.user.id)

    return render(
        request,
        "inventory/booking_list.html",
        {
            "grouped_bookings": grouped_bookings,
            "show_user": True,
            "view_filter": view_filter,
        },
    )



@login_required
def edit_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if booking.user != request.user and not request.user.is_staff:
        messages.error(request, "You are not allowed to edit this booking.")
        return redirect("booking_list")

    group_bookings = None
    if booking.booking_group:
        group_bookings = Booking.objects.filter(booking_group=booking.booking_group)

    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)

        if group_bookings:
            # Grouped bookings keep their original assets; edit applies to dates/purpose.
            form.fields["asset"].disabled = True

        if form.is_valid():
            if group_bookings:
                start_date = form.cleaned_data["start_date"]
                end_date = form.cleaned_data["end_date"]
                purpose = form.cleaned_data["purpose"]
                group_ids = list(group_bookings.values_list("id", flat=True))

                for grouped_booking in group_bookings:
                    overlapping = Booking.objects.filter(
                        asset=grouped_booking.asset,
                        start_date__lte=end_date,
                        end_date__gte=start_date,
                    ).exclude(pk__in=group_ids)

                    if overlapping.exists():
                        first = overlapping.first()
                        form.add_error(
                            None,
                            f"{grouped_booking.asset.name} is already booked between {first.start_date} and {first.end_date}.",
                        )

                if not form.non_field_errors():
                    group_bookings.update(start_date=start_date, end_date=end_date, purpose=purpose)
                    messages.success(request, "Grouped booking updated successfully.")
                    return redirect("booking_list")
            else:
                form.save()
                messages.success(request, "Booking updated successfully.")
                return redirect("booking_list")
    else:
        form = BookingForm(instance=booking)

        if group_bookings:
            form.fields["asset"].disabled = True

    return render(request, "inventory/edit_booking.html", {"form": form})


@login_required
def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.user = request.user
            message.save()
            send_mail(
                f"Contact Form: {message.subject}",
                (
                    f"Name: {message.name}\n"
                    f"Email: {message.email}\n"
                    f"Message: {message.message}"
                ),
                message.email,
                [admin[1] for admin in settings.ADMINS],
                fail_silently=False,
            )
            messages.success(request, "Message sent successfully.")
            return redirect("contact")
    else:
        form = ContactForm()
    return render(request, "inventory/contact.html", {"form": form})


def custom_page(request):
    return render(request, "inventory/custom_page.html")


def admin_required(user):
    return user.is_staff


@user_passes_test(admin_required)
def asset_create(request):
    if request.method == "POST":
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Asset created successfully.")
            return redirect("asset_list")
    else:
        form = AssetForm()
    return render(request, "inventory/asset_form.html", {"form": form})


@user_passes_test(admin_required)
def asset_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == "POST":
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, "Asset updated successfully.")
            return redirect("asset_list")
    else:
        form = AssetForm(instance=asset)
    return render(request, "inventory/asset_form.html", {"form": form})


@user_passes_test(admin_required)
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == "POST":
        asset.delete()
        messages.success(request, "Asset deleted successfully.")
        return redirect("asset_list")
    return render(request, "inventory/asset_confirm_delete.html", {"asset": asset})
