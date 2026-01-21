from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    # --- CÁC TRANG CHÍNH ---
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('news/<int:id>/', views.news_detail, name='news-detail'),
    path('category/<slug:slug>/', views.category_news, name='category_news'),
    path('search/', views.search_result, name='search-result'),
    
    # --- AI FEATURES ---
    path('transcribe/', views.transcribe_audio, name='transcribe'),
    path('summarize/<int:id>/', views.summarize_news, name='summarize_news'),

    # --- USER AUTH (LOGIN/LOGOUT/REGISTER) ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # --- TÍNH NĂNG LƯU TIN
    path('save-news/', views.save_news, name='save_news'),
    
    # --- TRANG XEM TIN ĐÃ LƯU ---
    path('saved-news/', views.saved_news, name='saved_news'),
    # API xoá tin đã lưu
    path('delete-saved-news/', views.delete_saved_news, name='delete_saved_news'),
    
    path('read-summary/', views.read_summary, name='read_summary'),
]

