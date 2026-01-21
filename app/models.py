from django.db import models
from django.conf import settings # Dùng để gọi bảng User mặc định của Django

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class News(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    )

    # Basic info
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    summary = models.TextField(blank=True, help_text="Short description / preview text")
    content = models.TextField()

    # Relations
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news",
    )
    # Đây là liên kết với bảng User (Tác giả bài viết)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news_articles",
    )

    # Media
    image = models.ImageField(
        upload_to="news/%Y/%m/%d/",
        null=True,
        blank=True,
    )

    # Meta / extra
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated tags, e.g.: tech, django, release",
    )
    source_url = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=255, blank=True)

    # Time
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "News"
        verbose_name_plural = "News"

    def __str__(self):
        return self.title


# ==================================================
# BẢNG MỚI: SAVED NEWS (LƯU TIN)
# ==================================================
class SavedNews(models.Model):
    """
    Bảng này lưu trữ việc User nào đã lưu Bài viết nào.
    """
    # Liên kết với bảng User (ID người dùng)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="saved_news"
    )
    
    # Liên kết với bảng News (ID bài viết)
    news = models.ForeignKey(
        News, 
        on_delete=models.CASCADE, 
        related_name="saved_by_users"
    )
    
    # Thời gian lưu
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Đảm bảo 1 user không thể lưu 1 bài viết 2 lần
        unique_together = ('user', 'news') 
        verbose_name = "Saved News"
        verbose_name_plural = "Saved News List"
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.user.username} saved {self.news.title}"