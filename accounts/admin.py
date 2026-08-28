"""Admin surface for customer accounts.

Read-only by design. Customers are created by signing up, not by staff, and
their phone number is their identity so it is never editable. The only field
staff can change is ``is_active`` (blocking), plus soft delete and restore as
bulk actions.
"""

from django.contrib import admin, messages
from django.utils import timezone
from djangoql.admin import DjangoQLSearchMixin
from unfold.admin import ModelAdmin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(DjangoQLSearchMixin, ModelAdmin):
    list_display = ("phone_number", "is_active", "is_deleted", "joined_at", "last_login")
    list_editable = ("is_active",)
    list_filter = ("is_active", "joined_at")
    search_fields = ("phone_number",)
    date_hierarchy = "joined_at"
    readonly_fields = ("id", "phone_number", "joined_at", "last_login", "deleted_at")
    fields = ("id", "phone_number", "is_active", "joined_at", "last_login", "deleted_at")
    actions = ("soft_delete_customers", "restore_customers")

    @admin.display(boolean=True, description="deleted")
    def is_deleted(self, obj):
        return obj.is_deleted

    def has_add_permission(self, request):
        # Accounts come into existence through signup only.
        return False

    def has_delete_permission(self, request, obj=None):
        # Orders reference customers; use the soft-delete action instead.
        return False

    @admin.action(description="Soft delete selected customers")
    def soft_delete_customers(self, request, queryset):
        updated = queryset.alive().update(deleted_at=timezone.now(), is_active=False)
        self.message_user(
            request,
            f"{updated} customer(s) soft deleted.",
            messages.SUCCESS if updated else messages.WARNING,
        )

    @admin.action(description="Restore selected customers")
    def restore_customers(self, request, queryset):
        updated = queryset.deleted().update(deleted_at=None, is_active=True)
        self.message_user(
            request,
            f"{updated} customer(s) restored.",
            messages.SUCCESS if updated else messages.WARNING,
        )
