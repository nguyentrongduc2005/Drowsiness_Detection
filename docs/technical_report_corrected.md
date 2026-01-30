# 2.1 Các kỹ thuật Thị giác máy tính nền tảng (Computer Vision Fundamentals)

## 2.1.1 Tổng quan về xử lý ảnh số trong giám sát tài xế

Trong hệ sinh thái ITS, dữ liệu hình ảnh là nguồn tài nguyên quan trọng nhất để phân tích hành vi thực thể.

- **Cơ chế thu nhận (Image Acquisition):** Sử dụng camera tiêu chuẩn (Webcam) thông qua giao diện OpenCV. Hệ thống hỗ trợ cấu hình độ phân giải (mặc định 640x480 hoặc 720p) và tốc độ khung hình (FPS) để đảm bảo khả năng xử lý thời gian thực.
- **Xử lý luồng dữ liệu (Stream Processing):** Duy trì tốc độ khung hình ổn định để giảm thiểu độ trễ phản hồi (Latency).
- **Tiền xử lý tối ưu (Preprocessing):**
  - **Color Space Conversion:** Chuyển đổi không gian màu từ BGR (mặc định của OpenCV) sang **RGB** (yêu cầu của MediaPipe). Khác với các phương pháp cũ dùng ảnh xám (Grayscale), MediaPipe tận dụng thông tin màu để trích xuất đặc trưng tốt hơn.
  - **Image Flipping:** Lật ảnh ngang (Mirror effect) để tạo trải nghiệm tự nhiên cho người dùng khi quan sát qua màn hình.

## 2.1.2 Các phương pháp phát hiện khuôn mặt (Face Detection Approaches)

Phát hiện khuôn mặt là bước nền tảng quyết định độ tin cậy của toàn hệ thống. Hệ thống hiện tại sử dụng công nghệ tiên tiến từ Google:

- **Phương pháp hiện tại (Google MediaPipe):** Thay vì sử dụng các phương pháp truyền thống như HOG+SVM, hệ thống sử dụng **MediaPipe Face Mesh**.
  - **BlazeFace Detector:** MediaPipe sử dụng một mô hình phát hiện khuôn mặt siêu nhẹ (lightweight) có tên là BlazeFace. Mô hình này được tối ưu hóa đặc biệt cho suy luận trên CPU di động (mobile GPU/CPU inference).
  - **Cơ chế hoạt động:** Sử dụng mạng SSD (Single Shot Detector) tùy chỉnh với cơ chế anchor scheme được tối ưu hóa, cho phép phát hiện khuôn mặt cực nhanh (sub-millisecond level).
- **Lý do chọn MediaPipe:**
  1.  **Hiệu suất thời gian thực (Real-time Performance):** Đạt tốc độ xử lý cao (30+ FPS) ngay cả trên CPU thông thường mà không cần GPU rời.
  2.  **Độ chính xác cao:** Khả năng định vị khuôn mặt tốt ngay cả khi khuôn mặt nghiêng, xoay hoặc bị che khuất một phần.
  3.  **Không cần tinh chỉnh thủ công:** Không cần các bước tiền xử lý phức tạp như cân bằng histogram thủ công vì mô hình đã được huấn luyện trên dữ liệu đa dạng.

## 2.1.3 Mô hình trích xuất đặc trưng khuôn mặt (Facial Landmark Detection)

Sau khi định vị khuôn mặt, hệ thống thực hiện trích xuất các điểm mốc hình học chi tiết.

- **Mô hình Face Mesh (468 Landmarks):** Thay vì chỉ sử dụng 68 điểm như Dlib (iBUG 300-W), MediaPipe Face Mesh cung cấp lưới hình học dày đặc gồm **468 điểm mốc 3D** trên khuôn mặt.
- **Trích xuất vùng quan tâm (ROI Extraction):** Từ lưới 468 điểm, hệ thống trích xuất các điểm quan trọng cụ thể để tính toán:
  - **Mắt trái & Mắt phải:** Tập hợp các điểm viền mắt để tính EAR.
  - **Miệng:** Tập hợp các điểm viền môi (Outer lip) để tính MAR.
- **Ưu điểm:** Độ ổn định (Jitter filtering) tốt hơn nhiều so với các thuật toán Cascade Regression Trees cũ, giúp giảm thiểu báo động giả do rung lắc camera.

# 2.2 Cơ sở lý thuyết về hành vi và chỉ số buồn ngủ (Drowsiness Theory)

## 2.2.1 Định nghĩa sinh trắc học về sự buồn ngủ (Biometric definitions)

Trong nghiên cứu giám sát tài xế, buồn ngủ được nhận diện thông qua các dấu hiệu sinh trắc học liên quan đến hành vi thị giác:

- **Tần suất chớp mắt:** Khi cơ thể mệt mỏi, tần suất chớp mắt thường tăng bất thường hoặc trở nên chậm và kéo dài (blink duration).
- **Thời gian nhắm mắt:** Người buồn ngủ có xu hướng nhắm mắt lâu hơn bình thường (microsleeps), dẫn đến giảm khả năng quan sát đường.
- **Hành vi ngáp:** Ngáp dài và liên tục là một chỉ số trực quan rõ ràng của sự mệt mỏi, thường đi kèm với giảm tập trung.

## 2.2.2 Lý thuyết về Tỉ lệ mắt (Eye Aspect Ratio - EAR)

EAR là chỉ số hình học được sử dụng để đánh giá trạng thái mở/nhắm của mắt.

- **Cơ sở hình học:** EAR được tính toán dựa trên tọa độ các điểm mốc của mắt (p1...p6) được trích xuất từ Face Mesh.
- **Công thức toán học:** Sử dụng khoảng cách Euclid (L2 Norm) giữa các điểm mí trên-dưới chia cho khoảng cách giữa hai góc mắt.
- **Mối quan hệ với trạng thái mắt:** Khi mắt mở, EAR duy trì ở mức cao. Khi mắt nhắm, khoảng cách dọc giảm mạnh → EAR giảm xuống dưới ngưỡng (Threshold) định trước (ví dụ: 0.25).

## 2.2.3 Lý thuyết về Tỉ lệ miệng (Mouth Aspect Ratio - MAR)

MAR là chỉ số hình học dùng để phát hiện hành vi ngáp.

- **Cấu trúc hình học:** MAR dựa trên các landmarks viền môi trên và dưới.
- **Công thức toán học:** Tính tỷ lệ giữa chiều cao mở miệng (khoảng cách môi trên-dưới) và chiều rộng miệng (khoảng cách mép trái-phải).
- **Ngưỡng phát hiện ngáp:** Khi MAR vượt qua một giá trị threshold nhất định (ví dụ: 0.65), hệ thống xác định hành vi ngáp.

# 2.3 Hệ thống cảm biến và công cụ phát triển (System & Tools)

## 2.3.1 Hệ thống phần cứng (Sensor Systems)

Trong hệ thống giám sát buồn ngủ, phần cứng đóng vai trò nền tảng để thu nhận và truyền tải dữ liệu:

- **Camera Sensor:** Camera là thành phần chính để ghi lại hình ảnh khuôn mặt tài xế. Yêu cầu cơ bản là độ phân giải tối thiểu 640x480 hoặc 720p. Hệ thống yêu cầu webcam hỗ trợ giao thức UVC tiêu chuẩn.
- **Audio Output:** Loa máy tính hoặc thiết bị phát âm thanh tích hợp để đưa ra cảnh báo trực tiếp (file âm thanh `alarm.wav`).

## 2.3.2 Môi trường và công cụ phát triển

Bên cạnh phần cứng, phần mềm và công cụ phát triển quyết định khả năng triển khai và hiệu quả của hệ thống:

- **Ngôn ngữ Python:** Được lựa chọn nhờ cú pháp đơn giản và hệ sinh thái mạnh mẽ cho AI.
- **Thư viện:**
  - **OpenCV (opencv-python):** Dùng để đọc stream từ camera, xử lý ảnh cơ bản (resize, flip, vẽ giao diện overlay).
  - **MediaPipe:** Thư viện lõi thay thế cho Dlib, cung cấp giải pháp Face Mesh tốc độ cao và chính xác.
  - **Pygame:** Sử dụng module `pygame.mixer` để xử lý phát âm thanh cảnh báo đa luồng (asynchronous audio playback) mà không làm chặn (block) luồng xử lý chính.
- **PyQt5 Framework:** Dùng để xây dựng giao diện người dùng (GUI).
  - **QThread:** Sử dụng đa luồng để tách biệt luồng xử lý AI (Detection Engine) và luồng giao diện (Main Window), đảm bảo giao diện không bị treo (freeze) khi thuật toán đang tính toán.
  - **Signal-Slot:** Cơ chế giao tiếp sự kiện để cập nhật trạng thái cảnh báo từ Engine lên giao diện.

# 2.4 Phân tích yêu cầu hệ thống (System Requirements Analysis)

## 2.4.1 Đặc tả tác nhân và kịch bản sử dụng (Actors & User Scenarios)

Các tác nhân (Actors):

- **Tài xế (Primary Actor):** Đối tượng cung cấp dữ liệu sinh trắc học và nhận cảnh báo.
- **Hệ thống giám sát (System):** Thực thể thu thập, xử lý và cảnh báo.

Kịch bản tương tác thực tế trong Code:

**Kịch bản 1: Trạng thái lái xe bình thường (Normal Monitoring)**

- **Bối cảnh:** Tài xế đang tỉnh táo, mắt mở tập trung (EAR > ngưỡng an toàn) và miệng khép hoặc nói chuyện bình thường (MAR < ngưỡng ngáp).
- **Diễn biến:** Hệ thống liên tục thu thập frames, tính toán các chỉ số EAR và MAR. Các giá trị này nằm trong phạm vi an toàn.
- **Phản hồi hệ thống:** Giao diện hiển thị video với lưới Face Mesh. Trạng thái hiển thị là "Normal" với khung viền và chữ màu xanh lá cây (Green). Không có âm thanh cảnh báo nào được phát ra.

**Kịch bản 2: Cảnh báo Mệt mỏi (Fatigue Warning)**

- **Bối cảnh:** Tài xế bắt đầu có dấu hiệu xuống sức, biểu hiện qua hành vi ngáp nhiều lần hoặc chớp mắt bất thường trong vòng 1 phút gần đây.
- **Diễn biến:** Hệ thống phân tích lịch sử hành vi trong cửa sổ thời gian 60 giây. Nếu phát hiện số lượng ngáp (Yawn Count) >= 2 lần hoặc tần suất chớp mắt (Blink Rate) rơi vào vùng bất thường (quá thấp < 10 hoặc quá cao >= 20), hệ thống xác định đây là dấu hiệu mệt mỏi tích lũy.
- **Phản hồi hệ thống:** Hệ thống chuyển sang trạng thái cảnh báo mức độ 1 (Fatigue). Giao diện hiển thị thông báo "Warning: Fatigue" với màu vàng (Yellow). Đây là cảnh báo nhắc nhở sớm, chưa kích hoạt còi báo động khẩn cấp.

**Kịch bản 3: Cảnh báo Ngủ gật (Drowsiness Alert)**

- **Bối cảnh:** Tài xế rơi vào trạng thái nguy hiểm: nhắm mắt hoặc ngủ gật (microsleep) trong khi đang điều khiển phương tiện.
- **Diễn biến:** Chỉ số EAR giảm mạnh xuống dưới ngưỡng thiết lập (ví dụ: EAR < 0.25) và duy trì liên tục trong một khoảng frames nhất định (Consecutive Frames >= 20). Hệ thống ưu tiên phát hiện này cao hơn trạng thái mệt mỏi.
- **Phản hồi hệ thống:** Hệ thống kích hoạt trạng thái khẩn cấp (Alert Level 2). Màn hình nhấp nháy hoặc hiển thị khung đỏ (Red) với dòng chữ lớn "WARNING: DROWSY!". Đồng thời, hệ thống phát âm thanh báo động lớn (file `alarm.wav`) liên tục qua loa để đánh thức tài xế ngay lập tức.

## 2.4.2 Yêu cầu chức năng (Functional Requirements)

| ID        | Chức năng (Feature)             | Mô tả chi tiết (Technical Specification)                                                                                                                                                    | Luồng dữ liệu (Data Flow)                                                |
| :-------- | :------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------------------------------- |
| **FR-01** | **Video Stream Acquisition**    | Thu nhận luồng video thời gian thực từ Webcam via OpenCV. Hỗ trợ cấu hình độ phân giải (Mặc định 640x480, Scaleable lên 720p) và FPS.                                                       | In: Raw Light signal<br>Out: Digital Frames (RGB)                        |
| **FR-02** | **Face Localization**           | Sử dụng **MediaPipe BlazeFace** (Deep Learning lightweight) để phát hiện khuôn mặt nhanh chóng. Thay thế cho phương pháp cũ HOG+SVM để tăng tốc độ trên CPU.                                | In: Digital Frames (RGB)<br>Out: Face ROI (Region of Interest)           |
| **FR-03** | **Facial Landmark Extraction**  | Áp dụng mô hình **Face Mesh** để tạo lưới **468 điểm mốc 3D**. Trích xuất các tập hợp điểm con cho mắt (Eye contours) và miệng (Lip contours).                                              | In: Face ROI<br>Out: 468 Coordinates Vector                              |
| **FR-04** | **Biometric Signal Processing** | Tính chỉ số EAR (Mắt) và MAR (Miệng) từ các điểm mốc. Logic phát hiện: So sánh với ngưỡng (Threshold) + Phân tích chuỗi thời gian (60s window cho mệt mỏi, consecutive frames cho ngủ gật). | In: Coordinates Vector<br>Out: Behavioral Status (Normal/Fatigue/Drowsy) |
| **FR-05** | **Multi-modal Alert System**    | Hệ thống phản hồi đa phương thức: Phát âm thanh cảnh báo (Wave) qua Pygame Mixer và hiển thị cảnh báo màu sắc/text trên giao diện PyQt5.                                                    | In: Status Signal<br>Out: Audio/Visual Feedback                          |

## 2.4.3 Yêu cầu phi chức năng (Non-Functional Requirements)

- **Hiệu năng (Performance):** Tốc độ xử lý ổn định (xấp xỉ 30 FPS trên CPU hiện đại).
- **Tính khả dụng (Usability):** Giao diện PyQt thân thiện, hiển thị trực quan video và các chỉ số.
- **Độ ổn định:** Hệ thống có cơ chế tự động tìm kiếm camera (auto-scan camera index) và xử lý ngoại lệ khi mất kết nối.
