from django.urls import path

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
    path("contact/", views.contact, name="contact"),
]
