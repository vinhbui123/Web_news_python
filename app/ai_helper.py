import torch

import threading

from transformers import AutoModelForCausalLM, AutoTokenizer


# ==============================

# CẤU HÌNH

# ==============================

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"


_model = None

_tokenizer = None

_model_lock = threading.Lock()


# --- PROMPT 1: Dành cho tin dữ liệu (Kinh tế, Công nghệ, Khoa học, Thể thao) ---

PROMPT_STRICT_DATA = (
    "Bạn là trợ lý AI trích xuất dữ liệu tin tức chính xác.\n"
    "Nhiệm vụ: Viết báo cáo ngắn gọn dạng văn xuôi về các sự kiện và số liệu.\n"
    "Quy tắc:\n"
    "1. Định danh: Gắn đúng số liệu cho đúng 'Thực thể' (Người, Tổ chức...).\n"
    "2. Trung thực: Chỉ lấy số liệu có trong bài, KHÔNG suy diễn.\n"
    "3. Format: Viết thành đoạn văn liền mạch, KHÔNG gạch đầu dòng, KHÔNG đánh số."
)


# --- PROMPT 2: Dành cho tin dòng thời gian (Showbiz, Sự kiện, Đời sống) ---

PROMPT_NARRATIVE_TIMELINE = (
    "Nhiệm vụ: Tóm tắt bài báo thành một đoạn văn xuôi duy nhất.\n"
    "Yêu cầu nội dung (bắt buộc phải có):\n"
    "1. Nêu rõ TÊN nhân vật chính, TUỔI hoặc danh hiệu (nếu có).\n"
    "2. Giữ lại các CON SỐ cụ thể (tiền bạc, thời gian, số lượng).\n"
    "3. Giữ lại một CẢM XÚC hoặc CÂU NÓI quan trọng nhất trong bài.\n"
    "4. Tuyệt đối KHÔNG gạch đầu dòng. Viết liền mạch, trôi chảy."
)

# Danh sách các Tags thiên về kể chuyện/mô tả (Dựa trên database)

# Lưu ý: Viết thường (lowercase) để so sánh cho chính xác

NARRATIVE_TAGS = {
    "entertainment",  # Bao gồm cả từ gốc và từ bị typo trong DB
    "lifestyle",
    "culture",
    "politics",
    "laws",
    "lifestyle",
}


def get_device():
    """Ưu tiên CUDA nếu có."""

    return "cuda" if torch.cuda.is_available() else "cpu"


def load_model_resources():
    """Load model + tokenizer (Singleton)."""

    global _model, _tokenizer

    if _model is not None and _tokenizer is not None:

        return _model, _tokenizer

    with _model_lock:

        if _model is not None and _tokenizer is not None:

            return _model, _tokenizer

        device = get_device()

        print(f" [AI] Loading {MODEL_ID} on {device.upper()}...")

        try:

            _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
            dtype = torch.float16 if device == "cuda" else torch.float32
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                torch_dtype=dtype,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )

            _model.eval()

            print(" [AI] Model loaded successfully")

            return _model, _tokenizer

        except Exception as e:

            print(f" [AI] Load model failed: {e}")

            return None, None


def select_prompt_by_tags(tags_str):
    """

    Kiểm tra tags để chọn Prompt phù hợp.

    Input: Chuỗi tags (vd: "Technology, AI") hoặc Tên Category

    Output: Prompt System

    """

    if not tags_str:

        return PROMPT_STRICT_DATA  # Mặc định nếu không có tag

    # Chuẩn hóa: chuyển về chữ thường, tách dấu phẩy nếu có

    tags_list = [t.strip().lower() for t in tags_str.split(",")]

    is_narrative = False

    for tag in tags_list:

        if tag in NARRATIVE_TAGS:

            is_narrative = True

            break

    if is_narrative:

        print(f" [Logic] Phát hiện tag '{tag}' -> Chế độ Kể chuyện (Narrative).")

        return PROMPT_NARRATIVE_TIMELINE

    else:

        print(f" [Logic] Tags '{tags_str}' -> Chế độ Phân tích số liệu (Strict Data).")

        return PROMPT_STRICT_DATA


def run_summarization(text: str, tags: str = "") -> str:
    """

    Tóm tắt bài báo thông minh.
    Args:
        text: Nội dung bài báo.
        tags: Chuỗi tags hoặc tên Category từ Database.

    """

    if not text or len(text.strip()) < 50:

        return "Nội dung quá ngắn."

    model, tokenizer = load_model_resources()

    if not model or not tokenizer:

        return "Hệ thống AI chưa sẵn sàng."

    device = get_device()

    # --- BƯỚC 1: CHỌN PROMPT DỰA TRÊN TAGS ---

    selected_system_prompt = select_prompt_by_tags(tags)

    # Giới hạn input

    MAX_INPUT_CHARS = 6000

    if len(text) > MAX_INPUT_CHARS:

        text = text[:MAX_INPUT_CHARS] + "..."

    messages = [
        {"role": "system", "content": selected_system_prompt},
        {"role": "user", "content": f"Văn bản:\n{text}\n\nTóm tắt:"},
    ]

    try:

        prompt_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        inputs = tokenizer(
            prompt_text, return_tensors="pt", max_length=4096, truncation=True
        ).to(device)

        # phần setting parameter để tối ưu sinh văn bản

        with torch.no_grad():

            outputs = model.generate(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                num_beams=3,
                # num_beams để tăng chất lượng sinh văn bản sử dụng thuật toán tham lam tăng nhiều thì giảm tốc độ và không hiệu quả, it quá thì văn bản kém chất lượng
                length_penalty=1.0,
                # length_penalty để điều chỉnh độ dài câu trả lời
                repetition_penalty=1.2,
                # repetition_penalty để giảm lặp lại từ nếu tăng cao quá sẽ làm văn bản khó hiểu gây halucination cho mô hình
                min_new_tokens=100,
                # min_new_tokens số từ sinh ra tối thiểu
                max_new_tokens=400,
                # max_new_tokens số từ sinh ra tối đa
                early_stopping=True,
                # early_stopping để dừng sinh khi đạt điều kiện
                do_sample=False,
                # do_sample false để không sử dụng sampling mà dùng beam search
            )

        generated = outputs[0][inputs.input_ids.shape[-1] :]

        summary = tokenizer.decode(generated, skip_special_tokens=True)

        return summary.strip()

    except Exception as e:
        print(f" [AI] Error: {e}")
        return "Lỗi xử lý."
