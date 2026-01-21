import json
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings

# --- CÁC IMPORT CHO AUTHENTICATION (Đăng nhập/Đăng ký) ---
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import News, Category, SavedNews
from .ai_helper import run_summarization
from .voice_helper import process_audio_file

from django.http import JsonResponse
from .tts_helper import text_to_speech
import uuid

# ==================================================
# MAIN PAGES
# ==================================================
def home(request):
    categories = Category.objects.all()

    # Lấy 5 tin mới nhất (Status = published)
    latest_news = News.objects.filter(status="published").order_by("-published_at")[:5]

    # Lấy tin theo từng chuyên mục (cần đảm bảo tên category trong DB khớp với chuỗi này)
    sports_news = News.objects.filter(category__name="Sports").order_by("-created_at")
    tech_news = News.objects.filter(category__name="Technology").order_by("-created_at")
    business_news = News.objects.filter(category__name="Economics").order_by(
        "-created_at"
    )
    lifestyle_news = News.objects.filter(category__name="Lifestyle").order_by(
        "-created_at"
    )

    # Tin phổ biến (xếp theo lượt xem)
    popular_news = News.objects.filter(status="published").order_by("-views")[:6]

    return render(
        request,
        "home.html",
        {
            "categories": categories,
            "latest_news": latest_news,
            "sports_news": sports_news,
            "tech_news": tech_news,
            "business_news": business_news,
            "lifestyle_news": lifestyle_news,
            "popular_news": popular_news,
        },
    )


def contact(request):
    categories = Category.objects.all()
    return render(request, "contact.html", {"categories": categories})


def news_detail(request, id):
    # Lấy tin chi tiết, tăng view nếu cần (ở đây chưa code tăng view)
    news = get_object_or_404(News, id=id, status="published")
    categories = Category.objects.all()
    return render(request, "news-detail.html", {"news": news, "categories": categories})


def search_result(request):
    query = request.GET.get("q")
    categories = Category.objects.all()
    results = []

    if query and query.strip():
        results = News.objects.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query),
            status="published",
        )

    return render(
        request,
        "search-result.html",
        {"query": query, "results": results, "categories": categories},
    )


def category_news(request, slug):
    category = get_object_or_404(Category, slug=slug)
    news_list = News.objects.filter(category=category, status="published").order_by(
        "-created_at"
    )
    categories = Category.objects.all()
    return render(
        request,
        "category-news.html",
        {"category": category, "news_list": news_list, "categories": categories},
    )


# ==================================================
# USER AUTHENTICATION (LOGIN / REGISTER / LOGOUT)
# ==================================================
def logout_view(request):
    logout(request)
    messages.success(request, "Đã đăng xuất thành công!")
    return redirect("home")


from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:
            login(request, user)
            messages.success(request, "Đăng nhập thành công!")
            messages.success(request, f"Chào mừng {user.username} quay trở lại!")
        else:
            messages.error(request, "Sai tài khoản hoặc mật khẩu!")

    return redirect("home")


def register_view(request):
    if request.method == "POST":
        # 1. Lấy dữ liệu từ HTML (theo name="...")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # 2. Kiểm tra dữ liệu (Validation)
        if password != confirm_password:
            messages.error(request, "Mật khẩu nhập lại không khớp.")
            return redirect("home")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Tên đăng nhập này đã tồn tại.")
            return redirect("home")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email này đã được sử dụng.")
            return redirect("home")

        # 3. Tạo tài khoản
        try:
            # create_user sẽ tự động mã hóa mật khẩu
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            user.save()

            # 4. Đăng nhập ngay lập tức
            login(request, user)
            messages.success(request, "Đăng ký thành công!")
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {e}")

    return redirect("home")


@login_required(login_url="home")  # Yêu cầu đăng nhập mới xem được
def saved_news(request):
    # Lấy danh sách tin đã lưu của user hiện tại, sắp xếp mới nhất lên đầu
    saved_list = SavedNews.objects.filter(user=request.user).order_by("-saved_at")

    # Lấy categories để hiển thị ở sidebar/footer như các trang khác
    categories = Category.objects.all()

    return render(
        request, "saved-news.html", {"saved_list": saved_list, "categories": categories}
    )


def save_news(request):
    """
    API nhận request AJAX để lưu bài viết
    """
    if request.method == "POST" and request.user.is_authenticated:
        try:
            # Lấy dữ liệu từ body request
            data = json.loads(request.body)
            news_id = data.get("news_id")

            # Lấy bài viết
            news_item = get_object_or_404(News, id=news_id)

            # Kiểm tra xem đã lưu chưa, nếu chưa thì tạo mới (get_or_create)
            obj, created = SavedNews.objects.get_or_create(
                user=request.user, news=news_item
            )

            if created:
                return JsonResponse(
                    {"success": True, "message": "Đã lưu bài viết thành công!"}
                )
            else:
                return JsonResponse(
                    {"success": False, "message": "Bạn đã lưu bài viết này rồi."}
                )

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse(
        {"success": False, "message": "Yêu cầu không hợp lệ hoặc chưa đăng nhập."},
        status=400,
    )


def delete_saved_news(request):
    """
    API xoá tin đã lưu (Bỏ lưu)
    """
    if request.method == "POST" and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            news_id = data.get("news_id")

            # Tìm bản ghi đã lưu của user hiện tại với bài viết đó
            saved_item = SavedNews.objects.filter(
                user=request.user, news_id=news_id
            ).first()

            if saved_item:
                saved_item.delete()
                return JsonResponse({"success": True, "message": "Đã bỏ lưu bài viết."})
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Bài viết này không có trong danh sách đã lưu.",
                    }
                )

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse(
        {"success": False, "message": "Yêu cầu không hợp lệ."}, status=400
    )


# ==================================================
# AI HELPERS (VOICE & SUMMARIZE)
# ==================================================
def transcribe_audio(request):
    """
    Endpoint xử lý Voice Search -> Gọi qua voice_helper
    """
    if request.method != "POST" or not request.FILES.get("file"):
        return JsonResponse({"error": "Yêu cầu không hợp lệ"}, status=400)

    audio_file = request.FILES["file"]

    # Kiểm tra dung lượng (Max 10MB)
    max_size = getattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024)
    if audio_file.size > max_size:
        return JsonResponse({"error": "File quá lớn (Max 10MB)"}, status=400)

    # --- GỌI HELPER XỬ LÝ ---
    result = process_audio_file(audio_file)

    # Xử lý kết quả trả về từ helper
    if "error" in result:
        status_code = result.get("code", 500)
        return JsonResponse({"error": result["error"]}, status=status_code)

    return JsonResponse(
        {
            "transcription": result["text"],
            "language": "vi",
            "model_used": result["model"],
            "duration": result["duration"],
        }
    )


def summarize_news(request, id):
    # Lấy bài viết, đảm bảo chỉ lấy bài đã published
    news_item = get_object_or_404(News, id=id, status="published")

    # Kiểm tra nội dung rỗng
    if not news_item.content:
        messages.error(request, "Bài viết rỗng, không thể tóm tắt.")
        return redirect("news-detail", id=id)

    # Kiểm tra đã có tóm tắt chưa (nếu muốn tóm tắt lại thì bỏ đoạn này hoặc thêm nút 'Force Update')
    if news_item.summary:
        messages.info(request, "Bài viết đã có tóm tắt.")
        return redirect("news-detail", id=id)

    try:
        messages.info(request, "AI đang đọc, phân tích ngữ cảnh và tóm tắt...")

        # --- BƯỚC 1: LẤY TAGS ĐỂ XÁC ĐỊNH NGỮ CẢNH (CONTEXT) ---
        # Ưu tiên lấy từ trường 'tags' của bài viết
        context_tags = news_item.tags if news_item.tags else ""

        # Nếu tags rỗng, dùng tên danh mục (Category) làm fallback
        if not context_tags and news_item.category:
            context_tags = news_item.category.name

        # --- BƯỚC 2: GỌI AI HELPER VỚI THAM SỐ TAGS ---
        # Truyền tags vào để AI chọn Prompt (Kể chuyện vs Số liệu)
        summary = run_summarization(news_item.content, tags=str(context_tags))

        # --- BƯỚC 3: LƯU KẾT QUẢ ---
        if summary and summary != "Lỗi xử lý.":
            news_item.summary = summary
            news_item.save(update_fields=["summary"])
            messages.success(request, "Tóm tắt thành công!")
        else:
            messages.error(request, "AI không trả về kết quả hợp lệ.")

    except Exception as e:
        print(f"AI Action Error: {e}")
        messages.error(request, f"Lỗi hệ thống khi gọi AI: {str(e)}")

    return redirect("news-detail", id=id)

def read_summary(request):
    """
    API nhận text hoặc ID bài viết, trả về link file mp3
    """
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        text = data.get("text", "")
        
        if not text:
            return JsonResponse({"error": "Không có nội dung"}, status=400)
            
        # Tạo tên file ngẫu nhiên để không bị trùng
        filename = f"audio_{uuid.uuid4()}.mp3"
        
        audio_url = text_to_speech(text, filename)
        
        if audio_url:
            return JsonResponse({"success": True, "audio_url": audio_url})
        else:
            return JsonResponse({"success": False, "message": "Lỗi tạo âm thanh"})
            
    return JsonResponse({"error": "Method not allowed"}, status=405)