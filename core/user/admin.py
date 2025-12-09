from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from core.user.models import UserProfile, UserAccount, TokenBlacklist

@admin.register(UserAccount)
class UserAccountAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'provider', 'created_at')
    list_filter = ('is_active', 'provider', 'created_at', 'is_verified')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('email',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('email', 'first_name', 'last_name')
        }),
        ('Seguridad', {
            'fields': ('password', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Social Auth', {
            'fields': ('provider', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_active'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions',)

admin.site.register(UserProfile)

@admin.register(TokenBlacklist)
class TokenBlacklistAdmin(admin.ModelAdmin):
    list_display = ('user','expires_at')

    def has_add_permission(self, request):
        return False  # No permitir agregar manualmente