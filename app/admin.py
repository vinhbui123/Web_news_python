from django.contrib import admin
from django.utils.html import format_html
from .models import Category, News, SavedNews

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'news_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

    # Hàm hiển thị số lượng bài viết trong mỗi danh mục
    def news_count(self, obj):
        return obj.news.count()
    news_count.short_description = 'Số bài viết'


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    # --- 1. Cấu hình hiển thị danh sách (List View) ---
    list_display = (
        'title', 
        'show_thumbnail', # Hiển thị ảnh nhỏ
        'category', 
        'author', 
        'status', 
        'is_featured', 
        'views', 
        'published_at'
    )
    list_filter = ('status', 'is_featured', 'category', 'created_at', 'author')
    search_fields = ('title', 'summary', 'tags')
    list_editable = ('status', 'is_featured') # Cho phép sửa nhanh
    # date_hierarchy = 'published_at'
    list_per_page = 20

    # --- 2. Tự động tạo slug ---
    prepopulated_fields = {'slug': ('title',)}

    # --- 3. Các trường chỉ đọc (không cho sửa) ---
    readonly_fields = ('views', 'created_at', 'updated_at', 'show_image_preview')

    # --- 4. Gom nhóm giao diện chi tiết (Detail View) ---
    fieldsets = (
        ('Thông tin chính', {
            'fields': ('title', 'slug', 'category', 'author', 'content', 'summary')
        }),
        ('Media', {
            'fields': ('image', 'show_image_preview', 'source_url')
        }),
        ('Cấu hình & Trạng thái', {
            'fields': ('status', 'is_featured', 'tags', 'published_at')
        }),
        ('SEO Meta', {
            'classes': ('collapse',), # Cho phép thu gọn mục này
            'fields': ('meta_title', 'meta_description')
        }),
        ('Thống kê (Read-only)', {
            'fields': ('views', 'created_at', 'updated_at')
        }),
    )

    # --- 5. Custom Actions (Thao tác hàng loạt) ---
    actions = ['make_published', 'make_draft']

    @admin.action(description='Đánh dấu là Đã xuất bản (Published)')
    def make_published(self, request, queryset):
        queryset.update(status='published')
        self.message_user(request, f"Đã xuất bản {queryset.count()} bài viết.")

    @admin.action(description='Đánh dấu là Bản nháp (Draft)')
    def make_draft(self, request, queryset):
        queryset.update(status='draft')
        self.message_user(request, f"Đã chuyển {queryset.count()} bài viết về bản nháp.")

    # --- 6. Hàm hỗ trợ hiển thị ảnh ---
    def show_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "-"
    show_thumbnail.short_description = 'Ảnh'

    def show_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px;" />', obj.image.url)
        return "(Chưa có ảnh)"
    show_image_preview.short_description = 'Xem trước ảnh'

    # Tự động gán author là user đang đăng nhập nếu chưa chọn
    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)
        
# Đăng ký bảng SavedNews
@admin.register(SavedNews)
class SavedNewsAdmin(admin.ModelAdmin):
    list_display = ('user', 'news', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('user__username', 'news__title')