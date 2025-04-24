"""
Script để tải và cài đặt font tiếng Việt cho việc xuất PDF
Font DejaVu Sans được sử dụng để hỗ trợ tiếng Việt
"""

import os
import requests
import zipfile
from io import BytesIO
import shutil

# URL tải font DejaVu Sans
DEJAVU_FONT_URL = "https://dejavu-fonts.github.io/Files/dejavu-fonts-ttf-2.37.zip"

# Đường dẫn thư mục hiện tại
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def download_and_extract_fonts():
    """Tải và giải nén font DejaVu Sans"""
    print("Bắt đầu tải font DejaVu Sans...")
    try:
        response = requests.get(DEJAVU_FONT_URL, stream=True)
        response.raise_for_status()
        
        print("Đã tải xong. Giải nén fonts...")
        
        # Giải nén file zip
        with zipfile.ZipFile(BytesIO(response.content)) as thezip:
            # Tìm các file font DejaVu Sans cần thiết
            dejavu_files = [file for file in thezip.namelist() if 
                           ('DejaVuSans.ttf' in file or 
                            'DejaVuSans-Bold.ttf' in file or
                            'DejaVuSans-Oblique.ttf' in file or
                            'DejaVuSans-BoldOblique.ttf' in file) and
                           file.endswith('.ttf')]
            
            # Giải nén các file đó vào thư mục hiện tại
            for file in dejavu_files:
                filename = os.path.basename(file)
                new_filename = filename.lower().replace('-', '-')
                
                # Đổi tên file theo định dạng chuẩn
                if 'DejaVuSans.ttf' in filename:
                    new_filename = 'dejavusans.ttf'
                elif 'DejaVuSans-Bold.ttf' in filename:
                    new_filename = 'dejavusans-bold.ttf'
                elif 'DejaVuSans-Oblique.ttf' in filename:
                    new_filename = 'dejavusans-oblique.ttf'
                elif 'DejaVuSans-BoldOblique.ttf' in filename:
                    new_filename = 'dejavusans-boldoblique.ttf'
                
                # Giải nén và lưu với tên mới
                with open(os.path.join(CURRENT_DIR, new_filename), 'wb') as f:
                    f.write(thezip.read(file))
                    print(f"Đã giải nén: {new_filename}")
        
        print("Hoàn tất cài đặt font!")
        
    except Exception as e:
        print(f"Lỗi: {str(e)}")
        print("Không thể tải font. Vui lòng thử lại sau hoặc tải thủ công.")

if __name__ == "__main__":
    download_and_extract_fonts() 