from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("assets/", views.asset_list, name="asset_list"),
    path("assets/add/", views.asset_create, name="asset_create"),
    path("assets/<int:pk>/edit/", views.asset_update, name="asset_update"),
    path("assets/<int:pk>/delete/", views.asset_delete, name="asset_delete"),
    path("book/", views.book_asset, name="book_asset"),
    path("bookings/", views.booking_list, name="booking_list"),
    path("bookings/<int:pk>/edit/", views.edit_booking, name="edit_booking"),
    path("bookings/<int:pk>/delete/", views.delete_booking, name="delete_booking"),
    path("contact/", views.contact, name="contact"),
    path("custom/", views.custom_page, name="custom_page"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
