# Hướng dẫn tự động cập nhật trạng thái bàn với đơn hàng

## Giới thiệu

Tính năng này đảm bảo trạng thái bàn luôn được đồng bộ với trạng thái đơn hàng, giúp quản lý nhà hàng hiệu quả hơn. Khi một bàn có đơn hàng đang xử lý, hệ thống sẽ tự động đánh dấu bàn đó là "đang có khách". Khi tất cả đơn hàng hoàn thành hoặc hủy, bàn sẽ được đánh dấu là "trống".

## Các tính năng chính

1. **Tự động cập nhật trạng thái bàn** khi tạo hoặc cập nhật đơn hàng
2. **Tự động chuyển đơn hàng thành "hoàn thành"** khi xuất hóa đơn
3. **Kiểm tra định kỳ** trạng thái bàn và đơn hàng để đảm bảo tính nhất quán
4. **Xử lý đơn hàng cũ** đã quá hạn để giữ hệ thống sạch sẽ

## Cách sử dụng

### 1. Cập nhật tự động khi thao tác trên Admin

Khi thêm, sửa, xóa đơn hàng trong trang Admin, hệ thống sẽ tự động:
- Đánh dấu bàn "đang có khách" khi có đơn hàng mới (pending/preparing)
- Đánh dấu bàn "trống" khi tất cả đơn hàng hoàn thành hoặc hủy

### 2. Cập nhật định kỳ với Script tự động

Để đảm bảo tính nhất quán của dữ liệu, bạn có thể thiết lập chạy script tự động theo lịch trình:

#### Sử dụng file `auto_update.py`:

```bash
# Di chuyển đến thư mục dự án
cd path/to/tomcafe_20/cafe_project

# Chạy script tự động
python auto_update.py
```

#### Thiết lập Windows Task Scheduler:

1. Mở Task Scheduler (Lịch biểu tác vụ)
2. Chọn "Create Basic Task" (Tạo tác vụ cơ bản)
3. Đặt tên và mô tả (ví dụ: "TomCafe Auto Update")
4. Chọn thời gian chạy (ví dụ: Daily - Hàng ngày)
5. Thiết lập thời điểm chạy (ví dụ: mỗi 30 phút)
6. Chọn "Start a program" (Khởi động một chương trình)
7. Nhập thông tin:
   - Program/script: `C:\path\to\python.exe`
   - Arguments: `C:\path\to\tomcafe_20\cafe_project\auto_update.py`
   - Start in: `C:\path\to\tomcafe_20\cafe_project`

#### Thiết lập Cron Job (Linux/Mac):

```bash
# Mở crontab
crontab -e

# Thêm dòng sau để chạy mỗi 30 phút
*/30 * * * * cd /path/to/tomcafe_20/cafe_project && python auto_update.py
```

### 3. Kiểm tra thủ công

Nếu bạn muốn kiểm tra và cập nhật trạng thái bàn ngay lập tức:

```bash
# Di chuyển đến thư mục dự án
cd path/to/tomcafe_20/cafe_project

# Chạy script kiểm tra
python checkdb.py
```

## Xem nhật ký (Log)

Tất cả các thao tác tự động được ghi lại trong file `auto_update.log`. Bạn có thể kiểm tra file này để theo dõi các thay đổi:

```bash
# Xem log
cat auto_update.log

# Xem 10 dòng log gần nhất
tail -n 10 auto_update.log
```

## Lưu ý

- Nhớ sao lưu dữ liệu trước khi sử dụng tính năng tự động cập nhật
- Nếu gặp lỗi, hãy kiểm tra file log để xác định nguyên nhân
- Có thể điều chỉnh thời gian kiểm tra đơn hàng cũ trong `auto_update.py` (mặc định là 3 ngày)

Nếu bạn cần hỗ trợ thêm, vui lòng liên hệ quản trị viên hệ thống.