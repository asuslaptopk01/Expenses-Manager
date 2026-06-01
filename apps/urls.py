from django.urls import path

from apps.views import main_page_view, edit_operation_view, delete_operation_view, register_view, \
    login_view, logout_view, otp_view, profile_edit_view, profile_delete_view, add_income_view, add_expense_view

urlpatterns = [
    path("", main_page_view, name="main"),
    path('income/add/', add_income_view, name='add-income'),
    path('expense/add/', add_expense_view, name='add-expense '),
    path('operations/<int:id>/edit/', edit_operation_view, name='edit-operation'),
    path('operations/<int:id>/delete/', delete_operation_view, name='delete-operation'),
    path("auth/register/", register_view, name="register"),
    path("auth/login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("auth/otp/", otp_view, name="otp"),
    path("profile/edit/", profile_edit_view, name="edit-profile"),
    path("profile/delete/", profile_delete_view, name="delete-profile"),
]