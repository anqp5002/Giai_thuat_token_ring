# Token Ring Lab

**Minh họa giải thuật loại trừ tương hỗ bằng thẻ bài (Token Ring)**

> Workload demo: mượn/trả thiết bị dùng chung. Vòng token là phần chính, mượn/trả chỉ là phần phụ để có tài nguyên tranh chấp.

Đồ án môn **Hệ thống phân tán**, nội dung 7: Loại trừ tương hỗ và giải thuật bầu cử.

## Mục tiêu

- Cài đặt giải thuật Token Ring chạy thật trên **4 laptop**, mỗi máy là một node; các node gửi message cho nhau qua TCP socket.
- Chỉ node đang giữ token mới được vào critical section (sửa trạng thái thiết bị).
- Cho thấy thuật toán chịu lỗi ra sao: mất token, token trùng, node sập, monitor sập, node gia nhập lại, phân mảnh mạng.
- Đo các số liệu để đối chiếu với lý thuyết: độ trễ trung bình N/2 chặng, thời gian một vòng quay, số message cho mỗi lần vào critical section.

## Thiết kế chính

- **Vòng logic:** 4 node (số node có thể cấu hình), token chuyền theo vòng.
- **State nằm trong token:** token mang theo trạng thái thiết bị kèm `state_version`. Mỗi node giữ một bản sao, nên không có file dùng chung và không có máy trung tâm.

```json
{
  "type": "TOKEN",
  "epoch": 3,
  "seq": 128,
  "holder": "May_2",
  "state_version": 57,
  "lamport": 342,
  "state": {
    "DEV-01": {"status": "BORROWED", "by": "May_2"},
    "DEV-02": {"status": "AVAILABLE", "by": null}
  }
}
```

- **Monitor** (lấy ý từ Active Monitor của IEEE 802.5): phát hiện mất token sau timeout và tạo lại token từ bản state mới nhất của các node còn sống.
- **Epoch:** token có epoch cũ bị hủy, nên token trễ mạng không gây ra hai token cùng lúc.
- **Bầu cử vòng** (Ring election, slide 7): khi monitor sập, các node bầu monitor mới.
- **Quorum = 3/4:** khi mạng bị chia cắt, bên nào không đủ quorum thì khóa thao tác Mượn/Trả.
- **JOIN_REQUEST:** node khởi động lại xin vào lại vòng và lấy state mới nhất.

## Giao diện

- **Mỗi máy:** ở giữa là sơ đồ vòng, vị trí token và nội dung token; một bên là bảng thiết bị; bên còn lại là Chaos Panel và log message thật (`TOKEN`, `ELECTION`, `JOIN`).
- **Observer view** (cho máy chiếu): toàn cảnh vòng, log của cả hệ thống và số liệu đo được.

## 12 trường hợp trình diễn

| TH | Nội dung | Kích hoạt |
|----|----------|-----------|
| TH1 | Vòng rảnh, token luân chuyển | Mở sẵn 4 máy |
| TH2 | Một máy mượn/trả | Thao tác bình thường trên 1 máy |
| TH3 | Tranh chấp đồng thời 1 máy chiếu | 4 người bấm Mượn cùng lúc; so sánh khi tắt và bật Token Ring |
| TH4 | Mất token | Nút "Hủy Token" |
| TH5 | Token cũ trễ mạng | Nút "Gửi lại Token cũ (Fake Lag)"; token epoch cũ bị hủy |
| TH6 | Máy thường sập lúc rảnh | Tắt app 1 máy; vòng nối tắt qua máy đó |
| TH7 | Máy sập lúc đang giữ token | Bật chế độ tự tắt app ngay khi nhận token |
| TH8 | Sập máy Monitor | Tắt app trên máy Monitor; bầu cử vòng chọn monitor mới |
| TH9 | Nhiều máy sập cùng lúc | Tắt 2 app cùng lúc; 2 máy còn lại vẫn chạy |
| TH10 | Máy khởi động lại, vào lại vòng | Mở lại app; `JOIN_REQUEST` và đồng bộ state |
| TH11 | Máy treo tạm thời | Nút "Đóng băng tiến trình 4s" |
| TH12 | Phân mảnh mạng 2-2 | Nút "Cô lập cụm"; cả 2 bên khóa Mượn/Trả vì không đủ quorum |

Kịch bản demo chia 3 hồi, khoảng 10 phút: **Vận hành bình thường** (TH1–3) → **Sự cố** (TH4–7) → **Hồi phục và phân mảnh** (TH8, TH10, TH12).

## Tài nguyên demo

- `DEV-01`: Máy chiếu Sony #01 (chỉ có 1 cái, nên thấy rõ tranh chấp)
- `DEV-02`, `DEV-03`: Kit Arduino #02, #03
- Vòng đời: `AVAILABLE` → `BORROWED` → `AVAILABLE`, dùng `state_version` và Lamport timestamp thay cho giờ hệ thống.

## Trạng thái

Mới khởi tạo repo, chưa có code.
