"""
File cấu hình cho PDF generator
Cấu hình font và các thông số khác cho hóa đơn PDF
"""

import os
from pathlib import Path

# Lấy đường dẫn gốc của dự án
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Cấu hình font cho PDF
PDF_FONT_CONFIG = {
    # Tên font chính sử dụng trong CSS
    'font_name': 'VietnamFont',
    
    # Đường dẫn đến font
    'font_path': os.path.join(BASE_DIR, 'cafe_project', 'static', 'fonts'),
    
    # Tên file font (thay thế bằng file TTF của bạn)
    'normal_font': 'custom-font.ttf',  # Font thường
    'bold_font': 'custom-font-bold.ttf',  # Font đậm
    
    # Encoding cho font
    'encoding': 'utf-8',
}

# Cài đặt màu sắc
PDF_COLORS = {
    'primary': '#6f4e37',  # Màu chính (nâu cà phê)
    'secondary': '#d4a76a',  # Màu phụ
    'text': '#333333',  # Màu chữ
    'heading': '#000000',  # Màu tiêu đề
}

# Các thông tin mặc định của quán
CAFE_INFO = {
    'name': 'TomCafe - Quản lý quán cà phê',
    'address': '312 Lý Thường Kiệt, TP.Đồng Hới, Quảng Bình',
    'phone': '0348287671',
    'email': 'tomcafe20@gmail.com',
}

# Hướng dẫn sử dụng:
"""
1. Thay thế các file font trong thư mục static/fonts
2. Cập nhật tên file font trong cấu hình PDF_FONT_CONFIG
3. Tùy chỉnh màu sắc và thông tin quán theo nhu cầu
"""

# Vietnamese font configuration
VIETNAMESE_FONT_CONFIG = {
    "pdf": {
        "fonts": {
            "dejavu": {
                "normal": "fonts/dejavusans.ttf",
                "bold": "fonts/dejavusans-bold.ttf",
                "italic": "fonts/dejavusans-oblique.ttf",
                "bolditalic": "fonts/dejavusans-boldoblique.ttf"
            }
        }
    }
} 