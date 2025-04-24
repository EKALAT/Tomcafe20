# TomCafe - Hệ thống quản lý quán cà phê

## Giới thiệu

TomCafe là một hệ thống quản lý quán cà phê toàn diện, được phát triển để đáp ứng nhu cầu vận hành hiệu quả của các quán cà phê vừa và nhỏ tại Việt Nam. Hệ thống này cung cấp các tính năng quản lý đơn hàng, bàn, danh mục thực đơn, và báo cáo doanh thu.

## Tính năng chính

- Quản lý thực đơn và danh mục
- Quản lý bàn và trạng thái bàn
- Xử lý đơn hàng và thanh toán
- Xuất hóa đơn PDF với hỗ trợ tiếng Việt đầy đủ
- Báo cáo doanh thu ngày/tháng với khả năng xuất Excel
- Quản lý khách hàng thân thiết
- Giao diện thân thiện, dễ sử dụng

## Hỗ trợ tiếng Việt

Hệ thống TomCafe hỗ trợ đầy đủ tiếng Việt trong các báo cáo xuất ra và hóa đơn. Chúng tôi cung cấp các công cụ để tự động cài đặt font chữ tiếng Việt và đảm bảo hiển thị chính xác trên mọi nền tảng.

### Tính năng hỗ trợ tiếng Việt

1. **Xuất hóa đơn PDF**: Sử dụng font DejaVu Sans và Roboto hỗ trợ đầy đủ các ký tự tiếng Việt
2. **Báo cáo Excel**: Hỗ trợ tiếng Việt trong báo cáo doanh thu ngày và tháng
3. **Cài đặt tự động**: Script `configure_fonts.py` tự động tải và cài đặt các font cần thiết

### Cách sử dụng hỗ trợ tiếng Việt

1. Chạy script cài đặt font:
   ```
   python configure_fonts.py
   ```

2. Khởi động lại máy chủ để áp dụng cài đặt mới

3. Tham khảo hướng dẫn chi tiết trong file `README_FONTS.md`

## Cài đặt hệ thống

### Yêu cầu

- Python 3.8+
- Django 3.2+
- Cơ sở dữ liệu: PostgreSQL hoặc SQLite 
- Các gói dependency khác trong file requirements.txt

### Các bước cài đặt

1. Clone repository:
   ```
   git clone https://github.com/tomcafe20/tomcafe-management.git
   cd tomcafe-management
   ```

2. Tạo và kích hoạt môi trường ảo:
   ```
   python -m venv venv
   source venv/bin/activate  # Trên Windows: venv\Scripts\activate
   ```

3. Cài đặt các gói phụ thuộc:
   ```
   pip install -r requirements.txt
   ```

4. Cài đặt font tiếng Việt:
   ```
   python configure_fonts.py
   ```

5. Cấu hình cơ sở dữ liệu trong `settings.py`

6. Thực hiện migrate để tạo cấu trúc database:
   ```
   python manage.py migrate
   ```

7. Tạo tài khoản admin:
   ```
   python manage.py createsuperuser
   ```

8. Chạy server phát triển:
   ```
   python manage.py runserver
   ```

9. Truy cập quản trị tại địa chỉ:
   ```
   http://127.0.0.1:8000/admin/
   ```

## Cấu trúc dự án

```
tomcafe_20/
├── cafe_project/            # Ứng dụng chính
│   ├── admin.py             # Giao diện quản trị
│   ├── dashboard.py         # Xử lý báo cáo và dashboard
│   ├── static/              # File tĩnh (CSS, JS, fonts)
│   └── templates/           # Template HTML
├── menu/                    # Quản lý thực đơn
├── orders/                  # Quản lý đơn hàng
├── tables/                  # Quản lý bàn
├── customers/               # Quản lý khách hàng
├── configure_fonts.py       # Script cài đặt font tiếng Việt
├── setup_vietnamese_fonts.py # Script cài đặt font tiếng Việt (phiên bản cũ)
└── requirements.txt         # Danh sách package cần thiết
```

## Hướng dẫn sử dụng

### Quản lý thực đơn

1. Truy cập menu quản trị
2. Chọn mục "Quản lý thực đơn"
3. Thêm danh mục và các món

### Quản lý đơn hàng

1. Tạo đơn hàng mới từ mục "Đơn hàng"
2. Chọn bàn và thêm món vào đơn
3. Cập nhật trạng thái đơn
4. Xuất hóa đơn khi hoàn thành

### Báo cáo doanh thu

1. Vào mục "Báo cáo" trên menu chính
2. Chọn loại báo cáo (ngày/tháng)
3. Xuất báo cáo ra Excel với đầy đủ tiếng Việt

## Ghi chú và FAQ

### Vấn đề về font tiếng Việt

Nếu gặp vấn đề về hiển thị tiếng Việt:
1. Đảm bảo đã chạy script cài đặt font `configure_fonts.py`
2. Kiểm tra thư mục `cafe_project/static/fonts/` đã có đủ các font
3. Tham khảo file `README_FONTS.md` để xử lý các vấn đề cụ thể

### Cần trợ giúp?

Nếu bạn cần hỗ trợ thêm, vui lòng liên hệ:
- Email: tomcafe20@gmail.com
- Điện thoại: 0348287671

## Tác giả

- Nhóm sinh viên TomCafe - Đại học Quảng Bình
- Email: tomcafe20@gmail.com

## License

TomCafe được phát hành theo giấy phép MIT. Xem file LICENSE để biết thêm chi tiết. 