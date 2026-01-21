import asyncio
import edge_tts
import os
from django.conf import settings

# Giọng đọc tiếng Việt: 
# 'vi-VN-HoaiMyNeural' (Nữ - Bắc)
# 'vi-VN-NamMinhNeural' (Nam - Bắc)
VOICE = 'vi-VN-HoaiMyNeural' 

async def generate_audio_async(text, output_file):
    """Hàm bất đồng bộ để gọi API của Edge-TTS"""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

def text_to_speech(text, filename="summary_audio.mp3"):
    """
    Hàm wrapper để chạy async trong môi trường sync của Django.
    Hàm này được gọi từ views.py
    """
    # 1. Xác định thư mục lưu file (media/tts)
    # Cần đảm bảo bạn đã cấu hình MEDIA_ROOT trong settings.py
    media_path = os.path.join(settings.MEDIA_ROOT, 'tts')
    
    # Tạo thư mục nếu chưa có
    os.makedirs(media_path, exist_ok=True)
    
    # Đường dẫn tuyệt đối để lưu file
    file_path = os.path.join(media_path, filename)
    
    # 2. Chạy hàm async để tạo file mp3
    try:
        asyncio.run(generate_audio_async(text, file_path))
        
        # 3. Trả về đường dẫn URL tương đối (vd: /media/tts/audio_xyz.mp3)
        # Để frontend có thể truy cập được
        return os.path.join(settings.MEDIA_URL, 'tts', filename)
    except Exception as e:
        print(f" [TTS Error] {e}")
        return None