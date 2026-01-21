import os
import shutil
import subprocess
import tempfile
import torch
from faster_whisper import WhisperModel

# ==============================
# CẤU HÌNH HỆ THỐNG
# ==============================
# Model size: "small" là lựa chọn tốt nhất cho CPU (nhanh và đủ khôn)
MODEL_SIZE = "small" 
_whisper_model = None

# Danh sách các câu vô nghĩa cần lọc bỏ
BAD_PHRASES = [
    "hãy đăng ký kênh", "cảm ơn đã xem", "subscribe", "like and share", 
    "phụ đề bởi", "vietsub", "copyright", "chúc các bạn", "video này"
]

# Danh sách sửa lỗi chính tả thủ công (AI hay nghe nhầm)
# Format: "từ sai": "từ đúng"
CORRECTIONS = {
    "công nghỉ": "công nghệ",
    "công nghê": "công nghệ",
    "đại hạn": "đại học",
    "sóc trăng": "Sóc Trăng",
    "việt nam": "Việt Nam",
    "trí tuệ nhân tạo": "trí tuệ nhân tạo",
    # Thêm các từ ngắn hay bị nhầm
    "tỉ": "tỷ",
    "kỉ": "kỷ",
    "di": "đi",
    "voi": "với",
    "cua": "của",
    "ma": "mà",
    "den": "đến",
    "tren": "trên",
    "duoi": "dưới",
    "cho": "cho",  # Đảm bảo không bị nhầm với chữ khác
    # Tên người nổi tiếng và cụm từ đặc biệt
    "sơn tùng mtb": "Sơn Tùng MTP",
    "sơn tùng em ti bi": "Sơn Tùng MTP",
    "sơn tùng m-tp": "Sơn Tùng MTP",
    "tuyển mê cho": "tuyến Metro",
    "tuyến mê cho": "tuyến Metro",
    "mê cho": "Metro",
    "metro": "Metro",
}

# Từ điển các từ ngắn thường gặp trong tin tức (giúp AI ưu tiên)
COMMON_SHORT_WORDS = [
    "về", "và", "từ", "tại", "theo", "cho", "của", "đã", "sẽ", "có", "là",
    "với", "trong", "ngoài", "trên", "dưới", "để", "khi", "nếu", "vì", "do",
    "bị", "được", "đang", "còn", "đến", "như", "mà", "hay", "hoặc", "nhưng"
]

def load_whisper_model():
    """
    Singleton Pattern: Chỉ load model 1 lần duy nhất khi server chạy.
    """
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    print(f" [Voice Helper] Loading Faster-Whisper ({MODEL_SIZE})...")
    
    # CHẾ ĐỘ AN TOÀN: Chạy trên CPU để tránh lỗi thiếu DLL của Nvidia
    device = "cpu"
    compute_type = "int8" # Tối ưu hóa cho CPU chạy nhanh hơn

    try:
        _whisper_model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
        print(f" [Voice Helper] Model loaded successfully on {device.upper()}")
        return _whisper_model
    except Exception as e:
        print(f" [Voice Helper] Load failed: {e}")
        return None

def get_audio_duration(path):
    """Lấy độ dài file âm thanh (giây) bằng ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def clean_text(text: str) -> str:
    """Làm sạch văn bản sau khi nhận diện"""
    text = text.strip()
    lower_text = text.lower()
    
    # 1. Lọc bỏ các cụm từ rác
    for p in BAD_PHRASES:
        if p in lower_text:
            return "" # Trả về rỗng nếu phát hiện rác
    
    # 2. Sửa lỗi chính tả từ từ điển CORRECTIONS
    # Cải tiến: Dùng word boundaries để tránh thay nhầm
    import re
    for wrong, right in CORRECTIONS.items():
        # Thay thế với word boundary để chính xác hơn
        pattern = r'\b' + re.escape(wrong) + r'\b'
        text = re.sub(pattern, right, text, flags=re.IGNORECASE)

    # 3. Xử lý dấu câu thừa
    text = text.replace(" .", ".").replace(" ,", ",")
    text = re.sub(r'\s+', ' ', text)  # Loại bỏ khoảng trắng thừa
    
    # 4. Xóa dấu chấm cuối câu
    text = text.rstrip('.')
    
    return text.strip()

def process_audio_file(uploaded_file):
    """
    Hàm chính: Nhận file từ Django request -> Convert -> Transcribe -> Trả về kết quả
    """
    model = load_whisper_model()
    if not model:
        return {"error": "AI Model not ready", "code": 503}

    # Tạo file tạm
    _, ext = os.path.splitext(uploaded_file.name)
    if not ext: ext = ".webm"

    tmp_input = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_wav.close() # Đóng để ffmpeg ghi vào

    try:
        # 1. Ghi nội dung upload vào file tạm
        for chunk in uploaded_file.chunks():
            tmp_input.write(chunk)
        tmp_input.close()

        # 2. Kiểm tra FFmpeg
        if shutil.which("ffmpeg") is None:
            return {"error": "Server missing FFmpeg", "code": 500}

        # 3. Convert sang chuẩn 16kHz Mono cho Whisper
        # CẢI TIẾN: Thêm filter normalize để cân bằng âm lượng (giúp nhận diện từ ngắn tốt hơn)
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", tmp_input.name,
            "-af", "silenceremove=start_periods=1:start_silence=0.2:start_threshold=-45dB,dynaudnorm=f=150:g=15",
            "-ar", "16000",
            "-ac", "1",
            tmp_wav.name,
        ]
        
        proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        # Nếu convert lỗi thì dùng file gốc (fallback)
        final_path = tmp_wav.name if proc.returncode == 0 else tmp_input.name
        
        # 4. Kiểm tra file sau xử lý
        if not os.path.exists(final_path) or os.path.getsize(final_path) < 100:
             return {"error": "Audio file too short or empty", "code": 422}

        duration = get_audio_duration(final_path)

        # 5. --- CHẠY FASTER-WHISPER (LOGIC CỐT LÕI) ---
        
        # PROMPT CẢI TIẾN: Thêm các từ ngắn thường gặp để AI học
        news_prompt = (
            "Đây là hệ thống tìm kiếm tin tức thời sự, chính trị, kinh tế, "
            "công nghệ thông tin, thể thao, bóng đá, giáo dục, khoa học kỹ thuật, "
            "xã hội, pháp luật tại Việt Nam. "
            f"Chú ý các từ thường gặp: {', '.join(COMMON_SHORT_WORDS[:15])}. "
            "Tìm kiếm từ khóa chính xác, bao gồm cả từ ngắn."
        )

        segments, info = model.transcribe(
            final_path,
            language="vi",            # Ép cứng tiếng Việt
            beam_size=10,             # Tăng từ 5 lên 10 để tìm kiếm kỹ hơn
            best_of=5,                # THÊM: Thử 5 hypothesis và chọn tốt nhất
            initial_prompt=news_prompt, # <--- QUAN TRỌNG: Gợi ý ngữ cảnh
            
            vad_filter=True,          # Lọc nhiễu/khoảng lặng
            vad_parameters=dict(
                min_silence_duration_ms=300,  # GIẢM từ 500->300 để nhạy hơn với từ ngắn
                threshold=0.5,
            ),
            
            condition_on_previous_text=False, # Tắt tính năng nhớ câu trước (tránh lặp)
            no_speech_threshold=0.5,   # GIẢM từ 0.6->0.5 để nhạy hơn
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,   # Chấp nhận xác suất thấp hơn cho từ ngắn
            word_timestamps=False
        )

        full_text = " ".join([s.text for s in segments])
        cleaned_text = clean_text(full_text)

        print(f" [AI Heard] Raw: '{full_text}' -> Clean: '{cleaned_text}'")

        if not cleaned_text:
            return {"error": "Could not recognize speech", "code": 422}

        return {
            "success": True,
            "text": cleaned_text,
            "duration": duration,
            "model": f"faster-whisper-{MODEL_SIZE}-cpu"
        }

    except Exception as e:
        print(f" [Voice Process Error] {e}")
        return {"error": str(e), "code": 500}

    finally:
        # Dọn dẹp file tạm để không rác ổ cứng
        try:
            if os.path.exists(tmp_input.name): os.remove(tmp_input.name)
            if os.path.exists(tmp_wav.name): os.remove(tmp_wav.name)
        except Exception:
            pass