from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Cafe, Category, Menu, Order, Set, Table, User


@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'phone',
        'address',
        'get_html_map_link',
        'get_html_photo',
    )

    def get_html_photo(self, object):
        if object.picture:
            return mark_safe(f'<img src="{object.picture.url}" width=100>')

    get_html_photo.short_description = 'Фото'

    def get_html_map_link(self, object):
        if object.map_link:
            return mark_safe(
                f'<a href="{object.map_link}">{object.map_link}</a>'
            )

    get_html_map_link.short_description = 'Ссылка на карту'


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'name', 'cost', 'get_html_photo')
    list_filter = ('category',)

    def get_html_photo(self, object):
        if object.picture:
            return mark_safe(f'<img src="{object.picture.url}" width=100>')

    get_html_photo.short_description = 'Фото'


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cafe',
        'table_number',
        'seats_count',
        'available',
    )
    list_filter = (
        'cafe',
        'available',
    )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'telegram_id',
        'name',
        'phone_number',
        'admin',
        'superuser',
    )
    search_fields = ('telegram_id', 'name', 'phone_number')
    list_filter = ('admin', 'superuser')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


# @admin.register(Booking)
# class BookingAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 'order', 'table',
#     )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'buyer',
        'date',
        'cafe',
        'from_date',
        'to_date',
        'guests',
        'is_paid',
        'is_cancelled',
    )
    list_filter = ('is_paid', 'is_cancelled', 'from_date')


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'set', 'quantity')


admin.site.site_title = 'AZUCafe telegram bot'
admin.site.site_header = 'AZUCafe telegram bot'
admin.site.index_title = 'Администрирование AZUCafe telegram bot'
admin.site.site_url = '/'
