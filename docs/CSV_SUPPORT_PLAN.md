# Kế hoạch triển khai hỗ trợ tệp CSV và Chọn Reader Động (Dynamic Reader Selection)

Bản kế hoạch này mô tả chi tiết việc thiết kế và lập trình bộ đọc dữ liệu CSV, xây dựng cơ chế tự động chọn bộ đọc (Reader Factory) dựa trên phần mở rộng (extension) của tệp tin, phân tích mức độ ảnh hưởng và quy trình xác thực.

---

## 1. Nội dung công việc triển khai

### Tầng Readers (Đọc file)
1. **Tạo mới lớp `CSVStreamReader`** (`src/readers/csv_reader.py`):
   * Đọc tệp CSV dạng stream (sử dụng thư viện chuẩn `csv` của Python kết hợp lập trình generator) để tối ưu hóa bộ nhớ tương tự bộ đọc Excel.
   * Kế thừa/triển khai giao thức Context Manager (`__enter__` và `__exit__`) để giải phóng tài nguyên hệ thống (file descriptor) tự động.
   * Hỗ trợ các thuộc tính cấu hình tương tự Excel:
     * `start_row`: Bỏ qua các dòng tiêu đề/metadata và bắt đầu đọc từ dòng chỉ định (1-based).
     * `skip_empty_rows`: Bỏ qua các hàng trống (chỉ chứa các giá trị rỗng/None).
     * `skip_patterns`: Bỏ qua các dòng chứa từ khóa tổng hợp/footer (tổng cộng, grand total, v.v.).
     * `delimiter` và `encoding`: Cho phép cấu hình bộ phân tách (mặc định là dấu phẩy `,`) và bảng mã ký tự (mặc định `utf-8`).
   * Triển khai hàm khởi tạo nhanh `from_mapping_config(cls, file_path, config)` tương thích trực tiếp với cấu hình `MappingConfig`.

2. **Xây dựng Factory chọn Reader Động** (`src/readers/__init__.py`):
   * Triển khai hàm `create_reader(file_path: str | Path, config: MappingConfig)` tự động nhận diện đuôi file:
     * Đuôi `.csv` -> Trả về thực thể `CSVStreamReader`.
     * Đuôi `.xlsx` hoặc `.xlsm` -> Trả về thực thể `ExcelStreamReader`.
     * Định dạng khác -> Ném ra lỗi `ValueError` kèm mô tả chi tiết.

### Tầng Pipeline (Đăng ký xử lý)
3. **Cập nhật luồng xử lý tệp tin** (`src/pipeline/ingestion_pipeline.py`):
   * Thay thế lệnh gọi trực tiếp `ExcelStreamReader.from_mapping_config` bằng hàm `create_reader` vừa xây dựng.

---

## 2. Ảnh hưởng đến luồng hệ thống (Impact Analysis)

### Downstream Flow (Luồng xử lý phía sau): **KHÔNG BỊ ẢNH HƯỞNG**
* Cả `CSVStreamReader` và `ExcelStreamReader` đều sẽ trả về các dòng dữ liệu dưới dạng `tuple` chuẩn của Python (ví dụ: `("TXN001", "100000", "SUCCESS")`).
* Do đó, các tầng Normalizer (chuẩn hóa kiểu dữ liệu, ghép cấu trúc `extra`), Validator (kiểm tra nghiệp vụ), và Persistence (lưu trữ MongoDB) hoàn toàn độc lập với nguồn gốc của tệp dữ liệu. Không cần bất kỳ thay đổi nào ở các bộ phận này.

### Cấu hình `MappingConfig` trong MongoDB: **KHÔNG BỊ ẢNH HƯỞNG**
* Hệ thống tiếp tục tái sử dụng cấu trúc `fieldMappings` hiện tại. Chỉ số cột (column index) hoặc tên cột ký tự vẫn được giữ nguyên và map chuẩn xác.
* Không đòi hỏi cập nhật cấu trúc schema của database.

---

## 3. Kế hoạch xác thực (Verification Plan)

### Kiểm thử tự động (Automated Tests)
1. **Viết mới file test chuyên biệt cho CSV** (`tests/test_csv_reader.py`):
   * Kiểm thử happy-path đọc file CSV chuẩn.
   * Kiểm thử tính năng bỏ qua dòng tiêu đề (`start_row`).
   * Kiểm thử tính năng lọc bỏ các dòng trống hoặc dòng chứa mẫu ký tự bỏ qua (`skip_patterns`).
   * Kiểm thử các tùy chọn bảng mã (`encoding`) và bộ phân tách tùy chỉnh (ví dụ: `;` hoặc tab `\t`).
2. **Kiểm thử tích hợp luồng pipeline**:
   * Kiểm thử tích hợp chạy thử luồng pipeline hoàn chỉnh đối với tệp CSV thật và cấu hình mock MongoDB.
3. **Chạy toàn bộ Suite kiểm thử**:
   * Chạy lệnh `uv run python -m pytest` để đảm bảo 100% tất cả 318 test cũ và các test CSV mới đều pass.

### Kiểm thử thủ công (Manual Verification)
* Viết script chạy thực tế để nạp thử cấu hình CSV của một đối tác ảo qua SFTP và kiểm tra dữ liệu lưu trên MongoDB.
