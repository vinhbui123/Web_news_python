from django import template

register = template.Library()

# Từ điển dịch (Mapping)
TRANS_DICT = {
    "Sports": "Thể thao",
    "Technology": "Công nghệ",
    "Business": "Kinh tế",
    "Economics": "Kinh tế",
    "Lifestyle": "Đời sống",
    "Culture": "Văn hóa",
    "Education": "Giáo dục",
    "Entertainment": "Giải trí",
    "Laws": "Pháp luật",
    "Politics": "Chính trị",
    "Science": "Khoa học",
    "Health": "Sức khỏe",
    "Travel": "Du lịch",
    "World": "Thế giới",
}

@register.filter(name='to_vietnamese')
def to_vietnamese(value):
    """
    Hàm nhận vào chuỗi tiếng Anh (value) và trả về tiếng Việt.
    Nếu không tìm thấy trong từ điển, trả về chính nó.
    """
    if not value:
        return ""
    # .get(key, default): Tìm key, nếu không có trả về default (chính nó)
    return TRANS_DICT.get(value.strip(), value)