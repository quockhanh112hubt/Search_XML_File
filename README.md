# XML Search Tool

Ứng dụng tìm kiếm file XML trên FTP Server với giao diện PyQt5

## Tính năng

- **Tìm kiếm thông minh**: Hỗ trợ text search, regex pattern và XPath query
- **Streaming search**: Đọc file theo chunk, không tải về đĩa cứng
- **Multi-threading**: Tìm kiếm song song với thread pool có thể cấu hình
- **Date range filter**: Lọc theo khoảng thời gian linh hoạt
- **File pattern filter**: Lọc file theo pattern (ví dụ: TCO_*_KMC_*.xml)
- **Export results**: Xuất kết quả ra CSV hoặc Excel
- **FTP Connection Pool**: Quản lý kết nối FTP hiệu quả với connection pooling

## Cấu trúc FTP Server

```
/SAMSUNG/
├── 20250827/
│   ├── Receive File/
│   └── Send File/          <- Target directory chứa XML files
│       ├── TCO_SEND_Data_N14_20250831234309_KMC_KMCEH19PL1.xml
│       ├── TCO_SEND_Data_N14_20250831234307_KMC_KMCEH19PL1.xml
│       └── ...
├── 20250828/
├── 20250829/
└── ...
```

## Cài đặt

1. **Clone repository**:
```bash
git clone https://github.com/quockhanh112hubt/Search_XML_File.git
cd Search_XML_File
```

2. **Cài đặt Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Chạy ứng dụng**:
```bash
python main.py
```

## Dependencies

- **PyQt5**: Giao diện người dùng
- **lxml**: XML parsing và XPath support
- **openpyxl**: Excel export
- **pandas**: Data manipulation và export
- **python-dateutil**: Date parsing utilities
- **ahocorasick**: Multi-string search algorithm

## Sử dụng

### 1. Cấu hình FTP Connection

1. Mở tab **Settings**
2. Nhập thông tin FTP:
   - FTP Host
   - Port (mặc định: 21)
   - Username
   - Password
3. Click **Test Connection** để kiểm tra kết nối

### 2. Thiết lập tìm kiếm

1. Mở tab **Search**
2. Chọn **Date Range**:
   - Quick ranges: Today, Yesterday, This Week, Last Week, etc.
   - Custom range: Chọn từ ngày đến ngày
3. Thiết lập **File Filter**:
   - File Pattern: `TCO_*_KMC_*.xml` (mặc định)
4. Nhập **Search Parameters**:
   - Keywords: Từ khóa tìm kiếm (mỗi dòng một từ)
   - Search Mode:
     - **Text Contains**: Tìm kiếm substring thông thường
     - **Regex Pattern**: Tìm kiếm theo regex pattern
     - **XPath Query**: Tìm kiếm theo XPath expression
   - Case Sensitive: Phân biệt hoa thường
   - Max Threads: Số luồng xử lý song song (1-20)

### 3. Thực hiện tìm kiếm

1. Click **Start Search**
2. Theo dõi tiến trình trong status bar
3. Xem kết quả trong tab **Results**
4. Click **Stop Search** để dừng nếu cần

### 4. Xuất kết quả

1. Mở tab **Results**
2. Click **Export CSV** hoặc **Export Excel**
3. Chọn vị trí lưu file

## Tối ưu hóa

### Search Strategy

- **Chunk Reading**: File được đọc theo chunk 256KB với overlap 1KB
- **Early Termination**: Dừng ngay khi tìm thấy match đầu tiên
- **Connection Pooling**: Tối đa 5 kết nối FTP đồng thời
- **Multi-threading**: Xử lý song song với thread pool có thể cấu hình

### Search Algorithms

- **Text Search**: Aho-Corasick algorithm cho multi-string matching
- **Regex Search**: Python re module với compiled patterns
- **XPath Search**: XML iterparse cho memory-efficient parsing

### File Size Limits

- Files > 50MB sẽ được bỏ qua (có thể cấu hình trong `config/settings.py`)
- Chunk size và overlap có thể điều chỉnh theo băng thông

## Cấu hình

Các cài đặt có thể điều chỉnh trong `config/settings.py`:

```python
# Threading Settings
MAX_WORKER_THREADS = 8
FTP_CONNECTION_POOL_SIZE = 5

# Search Settings
DEFAULT_CHUNK_SIZE = 256 * 1024  # 256KB
CHUNK_OVERLAP_SIZE = 1024  # 1KB
MAX_FILE_SIZE_MB = 50

# FTP Settings
FTP_TIMEOUT = 30
FTP_MAX_RETRIES = 3
```

## Logging

- Log files được lưu trong `xml_search.log`
- Log rotation: 10MB per file, giữ 5 backup files
- Log levels: DEBUG, INFO, WARNING, ERROR

## Architecture

```
src/
├── core/
│   ├── ftp_manager.py      # FTP connection management
│   ├── search_engine.py    # Search algorithms
│   └── search_worker.py    # Multi-threaded search coordinator
├── ui/
│   └── main_window.py      # PyQt5 main window
└── utils/
    ├── export_utils.py     # CSV/Excel export
    ├── date_utils.py       # Date parsing utilities
    └── logging_config.py   # Logging setup
```

## Testing

Chạy unit tests:

```bash
python -m pytest tests/ -v
```

Hoặc:

```bash
python tests/test_basic.py
```

## Troubleshooting

### FTP Connection Issues

1. Kiểm tra firewall và network connectivity
2. Đảm bảo FTP server hỗ trợ passive mode
3. Thử tăng timeout trong settings

### Memory Issues

1. Giảm số thread trong Max Threads
2. Giảm chunk size trong settings
3. Kiểm tra file size limits

### Search Performance

1. Sử dụng file pattern để giảm số file cần quét
2. Thu hẹp date range
3. Sử dụng text search thay vì regex khi có thể

## License

[MIT License](LICENSE)
