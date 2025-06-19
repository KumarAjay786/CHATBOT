# chat/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Conversation, Message
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('email', 'is_staff', 'is_active', 'last_chat_activity')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'chat_preferences')}),
        ('Permissions', {'fields': ('is_staff',
         'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'last_chat_activity')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2', 'is_staff',
                'is_active', 'groups', 'user_permissions'
            )}
         ),
    )
    search_fields = ('email',)
    ordering = ('email',)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('timestamp',)
    fields = ('is_user', 'content', 'timestamp')
    ordering = ('-timestamp',)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__email', 'title')
    inlines = [MessageInline]
    date_hierarchy = 'created_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('short_content', 'conversation', 'is_user', 'timestamp')
    list_filter = ('is_user', 'timestamp')
    search_fields = ('content', 'conversation__title')
    date_hierarchy = 'timestamp'

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'


admin.site.register(CustomUser, CustomUserAdmin)
