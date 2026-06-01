from django.contrib import admin
from django.contrib.admin import ModelAdmin

from apps.models import User, Operation, Category


# Register your models here.

@admin.register(User)
class UserAdmin(ModelAdmin):
    pass

@admin.register(Operation)
class OperationAdmin(ModelAdmin):
    pass

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    pass