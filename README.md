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

Nhóm dùng **bản gọn, bám slide**: state nằm trong token. Biểu quyết 3/4 chỉ dùng khi **đổi epoch** và **bầu Monitor**, không dùng cho từng thao tác mượn/trả (làm vậy phải dựng giao thức đồng thuận kiểu Raft, vượt nội dung 7).

- **Vòng logic:** 4 node `M1..M4` (số node có thể cấu hình), token chuyền theo vòng. Số ID 1..4 chỉ dùng để so sánh khi bầu cử.
- **State nằm trong token:** token mang theo trạng thái thiết bị kèm `state_version`. Mỗi node giữ một bản sao, nên không có file dùng chung và không có máy trung tâm.

```json
{
  "type": "TOKEN",
  "epoch": 3,
  "seq": 128,
  "holder": "M2",
  "state_version": 57,
  "lamport": 342,
  "state": {
    "DEV-01": {"status": "BORROWED", "borrowed_by": "M2"},
    "DEV-02": {"status": "AVAILABLE", "borrowed_by": null}
  }
}
```

- **Quy tắc ghi của bản gọn** (dùng chung cho mọi trường hợp):
  1. Máy giữ token chỉ được ghi khi thấy ít nhất 3/4 máy còn sống (theo heartbeat) và token có `epoch` bằng epoch hiện hành.
  2. Máy giữ token sửa `state`, tăng `state_version`, lưu bản sao cục bộ, rồi chuyển token đi.
  3. Thao tác chỉ được **báo thành công** khi máy kế tiếp đã ACK token mang state mới. Lúc đó state đã nằm trên ít nhất 2 máy.
  4. Mỗi máy lưu bản sao state mỗi khi token đi qua.
  5. Tạo lại token: xem mục Monitor bên dưới.
- **Giới hạn được thừa nhận:** nếu máy giữ token sập trước khi có ACK (bước 3) thì thao tác đó mất. Người dùng chưa nhận "thành công" nên gửi lại với cùng `request_id`; token mang danh sách `request_id` đã xử lý gần đây nên `request_id` trùng bị bỏ qua. Bản gọn không chống được mọi kiểu phân mảnh bất đối xứng.
- **Monitor** (lấy ý từ Active Monitor của IEEE 802.5): nghi mất token khi quá `TOKEN_TIMEOUT`. Monitor gửi `EPOCH_PROPOSE` (epoch + 1) cho các node; nếu **≥ 3/4 node đồng ý** (gửi kèm `state_version` của mình), Monitor sinh đúng một token mới từ state có `state_version` lớn nhất. Không đủ 3/4 thì không sinh token.
- **Epoch:** token có epoch cũ bị hủy, nên token trễ mạng không gây ra hai token cùng lúc.
- **Bầu cử vòng** (Ring election, slide 12): khi mất heartbeat của Monitor, một node gửi `ELECTION` theo vòng (bỏ qua node sập), mỗi node gắn ID của mình. Khi message quay về, node phát động gửi `COORDINATOR` kèm danh sách node sống; ID lớn nhất làm Monitor. Ví dụ Monitor là M4 tắt thì danh sách là {1,2,3} và M3 làm Monitor. Kết quả chỉ có hiệu lực khi danh sách có ≥ 3 node (quorum), nên phân mảnh 2-2 không bầu được Monitor nào.
- **Quorum = 3/4:** khi mạng bị chia cắt hoặc sập bớt máy, bên nào không đủ quorum thì khóa thao tác Mượn/Trả (chỉ xem).
- **JOIN_REQUEST:** node khởi động lại xin vào lại vòng và lấy state mới nhất.

## Giao diện

- **Mỗi máy:** ở giữa là sơ đồ vòng, vị trí token và nội dung token; một bên là bảng thiết bị; bên còn lại là Chaos Panel và log message thật (`TOKEN`, `ELECTION`, `JOIN`).
- **Observer view** (cho máy chiếu): toàn cảnh vòng, log của cả hệ thống và số liệu đo được.

## 14 trường hợp trình diễn (12 bắt buộc, TH13 và TH14 tùy chọn)

| TH | Nội dung | Kích hoạt | Kết quả mong đợi |
|----|----------|-----------|------------------|
| TH1 | Vòng rảnh, token luân chuyển | Mở sẵn 4 máy | Token chạy đều quanh vòng |
| TH2 | Một máy mượn/trả | Thao tác bình thường trên 1 máy | Thao tác thành công khi máy kế tiếp ACK |
| TH3 | Tranh chấp đồng thời 1 máy chiếu | 4 người bấm Mượn cùng lúc; so sánh khi tắt và bật Token Ring | Bật Token Ring: 1 người mượn được, 3 người bị từ chối; tắt (chế độ không an toàn): có thể nhiều người cùng mượn |
| TH4 | Mất token | Nút "Hủy Token" | Monitor đề xuất epoch + 1, đủ 3/4 đồng ý thì sinh token mới |
| TH5 | Token cũ trễ mạng | Nút "Gửi lại Token cũ (Fake Lag)" | Token epoch cũ bị hủy |
| TH6 | Máy thường sập lúc rảnh | Tắt app 1 máy | Vòng nối tắt qua máy đó; còn 3/4 nên vẫn Mượn/Trả được |
| TH7 | Máy sập lúc đang giữ token | Bật chế độ tự tắt app ngay khi nhận token | Tạo lại token theo TH4; thao tác chưa có ACK thì người dùng gửi lại cùng `request_id`, không bị ghi 2 lần |
| TH8 | Sập máy Monitor | Tắt app trên máy Monitor | Bầu cử vòng chọn Monitor mới |
| TH9 | Hai máy sập cùng lúc | Tắt 2 app cùng lúc | 2 máy còn lại nối vòng với nhau nhưng khóa Mượn/Trả vì 2/4 < quorum 3; chỉ xem. Mở lại 1 máy thì ghi trở lại |
| TH10 | Máy khởi động lại, vào lại vòng | Mở lại app | `JOIN_REQUEST` và đồng bộ state |
| TH11 | Máy treo tạm thời | Nút "Đóng băng tiến trình 4s" | Đóng băng 4s lâu hơn NODE_DEAD 3s nên máy bị loại khỏi vòng; hết đóng băng thì bỏ token/liên kết cũ, chuyển REJOINING và JOIN lại như TH10 |
| TH12 | Phân mảnh mạng 3-1 và 2-2 | Nút "Cô lập cụm" | 3-1: nhóm 3 máy ghi tiếp, máy lẻ chỉ xem; 2-2: cả hai bên chỉ xem |
| TH13 | (tùy chọn) Hợp nhất mạng | Bỏ cô lập | Nhóm thiểu số nhận epoch + state mới rồi vào lại vòng |
| TH14 | (tùy chọn) Mất token/ACK khi chuyển | Nút bỏ message ở tầng ứng dụng | Gửi lại cùng `seq`, bên nhận bỏ token trùng |

Kịch bản demo chia 3 hồi, khoảng 15 phút: **Vận hành bình thường** (TH1–3) → **Sự cố** (TH4–7, TH9) → **Hồi phục và phân mảnh** (TH8, TH10, TH11, TH12). TH13 và TH14 chỉ diễn nếu còn giờ.

## Tài nguyên demo

- `DEV-01`: Máy chiếu Sony #01 (chỉ có 1 cái, nên thấy rõ tranh chấp)
- `DEV-02`, `DEV-03`: Kit Arduino #02, #03
- Vòng đời: `AVAILABLE` → `BORROWED` → `AVAILABLE`, dùng `state_version` và Lamport timestamp thay cho giờ hệ thống.

## Phân công

Mỗi phần làm trên nhánh riêng (`core/...`, `fault/...`, `storage/...`, `ui/...`), qua Pull Request và cần 1 người khác review; không ai push thẳng lên `main`. Tên trường và tên message lấy đúng theo `docs/PROTOCOL.md` (đang viết); muốn đổi thì sửa PROTOCOL trước.

| Người | Phụ trách | File chính | Trường hợp |
|-------|-----------|------------|------------|
| Pham An | Lõi giao thức: `docs/PROTOCOL.md` (message, cổng, timeout, máy trạng thái node), `RingNode` gồm TCP, chuyển token, TOKEN_ACK, `seq`, epoch, quy tắc ghi; tích hợp cuối | `docs/PROTOCOL.md`, `token_ring.py` | TH1–TH5, TH14 |
| Ho Van Duc | Chịu lỗi: heartbeat, Monitor tạo lại token (EPOCH_PROPOSE/VOTE), bầu cử vòng, danh sách thành viên + quorum 3/4, JOIN_REQUEST; sửa tài liệu TH cho khớp bản gọn | `fault.py` (hoặc phần trong `token_ring.py`), `TONG_HOP...md` | TH6–TH13 |
| Khánh Duy Phạm | Lưu trữ + đồng bộ: SQLite `inventory.db` (devices, state_metadata, request_results, protocol_state), lưu bản sao mỗi lần token đi qua, bỏ `request_id` trùng, dữ liệu STATE_SYNC; đo số liệu (N/2 chặng, thời gian một vòng, message cho mỗi lần vào CS) | `storage.py`, `metrics.py`, `THIET_KE...md` | TH2, TH3, TH7, TH10 (phần dữ liệu) |
| HieuNguyen | Giao diện: màn hình từng máy, Observer view, Chaos Panel (Hủy Token, Fake Lag, tự tắt khi nhận token, Đóng băng 4s, Cô lập cụm); thay `DemoRing` bằng node thật; giữ chế độ mô phỏng 1 máy để tập demo | `token_ring_dashboard.py`, `chaos.py` | Nút kích hoạt cho mọi TH |

Thứ tự làm (có phụ thuộc):

1. Pham An chốt `docs/PROTOCOL.md` và giao diện `RingNode` (hàm `start`, `submit`, `receive`, callback sự kiện cho UI). Ba người kia chờ bước này để code khớp nhau.
2. Bốn người làm song song trên nhánh riêng.
3. Ghép trên 1 máy bằng chế độ mô phỏng, sau đó chạy thật trên 4 laptop theo 12 TH bắt buộc.
4. Tập demo theo 3 hồi (khoảng 15 phút); TH13 và TH14 chỉ diễn nếu kịp.

## Trạng thái

- `main`: mới có README, chưa có code.
- Nhánh `tv4/token-ring-dashboard`: có dashboard Tkinter nhưng **chưa chạy được** vì thiếu `token_ring.py` (`from token_ring import RingNode` báo ImportError).
- Nhánh `docs/tong-hop-cac-truong-hop-token-ring`: tài liệu tổng hợp các trường hợp (TH).
- Nhánh `docs/thiet-ke-du-lieu-kho`: thiết kế dữ liệu (DB).
- `docs/PROTOCOL.md`: đang viết.
