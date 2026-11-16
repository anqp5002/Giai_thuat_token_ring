# Tổng hợp các trường hợp kiểm thử ứng dụng mượn thiết bị sử dụng Token Ring — hệ thống 4 máy

## 1. Phạm vi và giả định chung

Tài liệu này tổng hợp các trường hợp cần trình diễn cho ứng dụng mượn thiết bị sử dụng Token Ring. Mục tiêu chính là giải thích dễ hiểu: hệ thống đang gặp tình huống gì, xử lý như thế nào, vì sao cần cách xử lý đó và kết quả nào được xem là đúng.

Các trường hợp bên dưới dựa trên các giả định sau:

- Có 4 máy chạy ứng dụng độc lập trên cùng mạng LAN, có ID từ 1 đến 4.
- Bốn máy tạo thành vòng logic `1 → 2 → 3 → 4 → 1` và truyền Token qua TCP.
- Mỗi máy giữ một bản sao trạng thái mượn/trả thiết bị.
- Chỉ máy đang giữ Token mới được quyền xác nhận thao tác làm thay đổi dữ liệu.
- Mỗi yêu cầu có `operation_id` duy nhất để tránh thực hiện trùng.
- Token có `token_epoch` để phân biệt Token hiện hành với Token cũ.
- Một máy giữ vai trò Monitor, chịu trách nhiệm theo dõi thành viên, điều phối phục hồi Token và tổ chức bầu chọn khi cần.
- Hệ thống dùng heartbeat để phát hiện máy không còn phản hồi.
- Khi mạng bị phân mảnh, chỉ cụm có quá bán, tức ít nhất 3 trong tổng số 4 máy, được phép mượn/trả. Cụm không đủ quá bán chỉ được đọc dữ liệu cục bộ; dữ liệu này có thể đã cũ.

**Ngưỡng 3/4 được giữ cố định:** loại máy khỏi vòng truyền Token không đồng nghĩa loại máy khỏi cấu hình biểu quyết. Không tự hạ ngưỡng xuống 2/3 hoặc 2/2 sau khi máy mất kết nối, vì có thể khiến hai cụm cùng có quyền ghi.

Để các kết quả chịu lỗi bên dưới đúng, mỗi thao tác chỉ được báo thành công sau khi được lưu bền vững và xác nhận bởi ít nhất 3/4 máy, tính cả máy xử lý. Máy nhận Token phải có trạng thái đã chốt mới nhất trước khi xử lý yêu cầu tiếp theo. Epoch và quyền của Monitor cũng phải được thống nhất qua quá bán; các bản ghi từ epoch cũ bị từ chối khi xác nhận. Chỉ đếm heartbeat hoặc chỉ khóa nút trên giao diện chưa đủ để bảo đảm an toàn.

Đây là tài liệu hành vi dự kiến để thiết kế và demo, chưa phải kết quả xác minh ứng dụng đã triển khai đủ các cơ chế đó.

> **Lưu ý:** Token Ring tự nó chỉ cung cấp quyền truy cập tuần tự. Các khả năng như phát hiện máy sập, chống Token cũ, bầu Monitor và chống phân mảnh cần thêm heartbeat, epoch, danh sách thành viên và cơ chế quá bán.

## 2. Bảng tổng hợp các trường hợp

| Trường hợp | Diễn biến trên ứng dụng | Cách kích hoạt khi demo | Kết quả mong đợi |
| --- | --- | --- | --- |
| **TH1. Vòng rảnh** | Không có yêu cầu mượn/trả. Mỗi máy nhận Token, kiểm tra hàng đợi rỗng rồi chuyển Token cho máy kế tiếp. | Mở sẵn 4 máy và chưa thực hiện thao tác nào. | Token tiếp tục đi đủ vòng `1 → 2 → 3 → 4 → 1`. |
| **TH2. Một máy mượn/trả** | Máy 1 đưa yêu cầu mượn `Arduino #02` vào hàng đợi. Khi Token đến, máy kiểm tra thiết bị, ghi nhận thao tác, đồng bộ trạng thái rồi chuyển Token. Thao tác trả cũng được xử lý theo quy trình tương tự. | Thực hiện mượn, sau đó trả thiết bị trên Máy 1. | Mỗi thao tác chỉ được ghi một lần và trạng thái mới xuất hiện trên tất cả máy. |
| **TH3. Tranh chấp đồng thời** | Bốn máy cùng yêu cầu mượn `Máy chiếu #01`. Các yêu cầu được xử lý lần lượt theo thứ tự nhận Token. | Đếm ngược để bốn người cùng bấm **Mượn**. | Một yêu cầu thành công; ba yêu cầu còn lại bị từ chối vì thiết bị đã được mượn. |
| **TH4. Mất Token** | Token bị hủy trong khi đang có yêu cầu chờ. Monitor xác minh Token không còn hoạt động, tăng epoch và sinh Token mới. | Bấm **Hủy Token** trước khi Token tới máy đang có yêu cầu. | Chỉ một Token thuộc epoch mới được đưa vào vòng; yêu cầu đang chờ tiếp tục được xử lý. |
| **TH5. Token cũ xuất hiện** | Một Token cũ đến trễ sau khi hệ thống đã tạo Token thế hệ mới. | Bấm **Gửi lại Token cũ (Fake Lag)**. | Máy nhận so sánh `token_epoch`, hủy Token cũ và không thực hiện yêu cầu bằng Token đó. |
| **TH6. Máy thường bị sập** | Máy 3 bị tắt khi không giữ Token. Máy đứng trước phát hiện mất heartbeat/ACK và tìm máy còn sống tiếp theo. | Tắt ứng dụng trên Máy 3. | Vòng được sửa từ `2 → 3 → 4` thành `2 → 4`; các máy còn lại tiếp tục hoạt động. |
| **TH7. Máy sập khi giữ Token** | Máy 3 bị tắt trong lúc đang xử lý yêu cầu bằng Token. Hệ thống kiểm tra nhật ký thao tác và phục hồi Token bằng epoch mới nếu cần. | Bật chế độ tự tắt Máy 3 ngay sau khi nhận Token. | Thao tác hoặc được ghi nhận đúng một lần, hoặc được thử lại an toàn; thiết bị không bị khóa vô thời hạn. |
| **TH8. Monitor bị sập** | Máy Monitor ngừng hoạt động. Các máy còn lại phát hiện mất heartbeat và chạy thuật toán bầu chọn. | Tắt máy đang có biểu tượng Monitor/Vương miện. | Một Monitor mới được chọn theo quy tắc đã công bố; vòng tiếp tục có một Monitor duy nhất. |
| **TH9. Hai máy liên tiếp bị sập** | Máy 2 và Máy 3 cùng ngừng hoạt động. Máy 1 có thể nối tới Máy 4 nhưng chỉ còn 2/4 máy. | Tắt đồng thời Máy 2 và Máy 3. | Khóa mượn/trả vì không đủ 3/4; chỉ đọc. Có thể phục hồi ghi sau khi máy thứ ba trở lại và hoàn tất phục hồi trạng thái. |
| **TH10. Máy khởi động lại** | Máy 3 mở lại, gửi `JOIN_REQUEST`, tải trạng thái và epoch mới nhất, sau đó mới được chèn vào vòng. | Mở lại Máy 3 sau TH6. | Máy 3 không đưa dữ liệu hoặc Token cũ trở lại hệ thống; sau đồng bộ, vòng lại có đủ bốn máy. |
| **TH11. Máy treo tạm thời** | Máy 4 ngừng phản hồi lâu hơn heartbeat timeout nên bị loại tạm thời. Khi hoạt động lại, máy chuyển sang trạng thái `REJOINING`. | Đóng băng Máy 4 lâu hơn ngưỡng timeout, ví dụ đóng băng 5 giây khi timeout là 3 giây. | Máy 4 không tiếp tục sử dụng Token hoặc liên kết cũ mà phải đồng bộ và xin gia nhập lại. |
| **TH12. Phân mảnh mạng** | Thử hai cách chia: `3–1` và `2–2`. Chỉ nhóm có ít nhất ba máy mới đủ điều kiện ghi. | Bấm **Cô lập cụm**, chặn toàn bộ liên lạc giữa hai nhóm. | Với `3–1`: nhóm ba máy tiếp tục sau phục hồi; máy đơn lẻ chỉ đọc. Với `2–2`: cả hai nhóm chỉ đọc. |
| **TH13. Hợp nhất mạng trở lại** | Kết nối giữa hai cụm được phục hồi. Hệ thống thống nhất Monitor, epoch và nhật ký đã chốt trước khi ghép vòng. | Bỏ chế độ cô lập sau TH12, thử cả `3–1` và `2–2`. | Token cũ bị vô hiệu; dữ liệu được đồng bộ trước khi bốn máy tạo lại một vòng thống nhất. |
| **TH14. Mất gói khi chuyển Token** | Máy gửi Token nhưng không nhận được ACK nên chưa biết Token hoặc ACK đã bị mất. | Mô phỏng bỏ gói Token hoặc bỏ ACK trong lúc chuyển Token. | Hệ thống dùng `transfer_id` để không xử lý lặp; nếu không thể xác định chủ Token, Monitor phục hồi bằng epoch mới. |

## 3. Giải thích chi tiết

### TH1. Vòng rảnh

Token phải tiếp tục luân chuyển ngay cả khi không có yêu cầu nghiệp vụ. Khi một máy nhận Token và thấy hàng đợi rỗng, máy chuyển Token ngay cho máy kế tiếp. Trường hợp này chứng minh cấu trúc vòng, kết nối giữa các máy và cơ chế chuyển Token đang hoạt động.

Đây cũng là trạng thái nền để khán giả quan sát được Token trước khi bắt đầu các tình huống phức tạp. Giao diện nên hiển thị máy đang giữ Token, đường đi của Token và số vòng đã hoàn thành.

### TH2. Một máy mượn/trả

Khi người dùng bấm mượn, ứng dụng không cập nhật dữ liệu ngay mà đưa yêu cầu vào hàng đợi. Khi máy nhận Token, nó thực hiện lần lượt các bước:

1. Kiểm tra yêu cầu chưa được xử lý thông qua `operation_id`.
2. Kiểm tra thiết bị đang ở trạng thái có thể mượn.
3. Ghi nhận người mượn và thời điểm mượn.
4. Đồng bộ thay đổi sang các máy khác.
5. Thông báo kết quả cho người dùng và chuyển Token.

Trả thiết bị là một thao tác ghi độc lập nên cũng phải chờ Token. Token không đại diện cho một thiết bị cụ thể; Token chỉ đại diện cho quyền thay đổi trạng thái dùng chung.

### TH3. Tranh chấp đồng thời

Bốn yêu cầu có thể được tạo gần như cùng lúc nhưng không được xử lý đồng thời. Máy nào có yêu cầu và nhận Token trước sẽ kiểm tra trạng thái thiết bị trước. Nếu yêu cầu đó hợp lệ, thiết bị chuyển sang trạng thái đã được mượn. Khi các yêu cầu còn lại lần lượt được xử lý, chúng đều nhìn thấy trạng thái mới và bị từ chối.

Nếu muốn so sánh với tình trạng không dùng Token, cần đặt tên rõ là **chế độ không an toàn**: không Token, không khóa và không kiểm soát phiên bản. Không nên khẳng định mọi hệ thống không dùng Token Ring đều cho cả bốn máy mượn thành công, vì cơ sở dữ liệu hoặc cơ chế khóa khác vẫn có thể chống tranh chấp. Ngay cả chế độ không an toàn cũng cần chủ động tạo độ trễ giữa bước đọc và ghi để lỗi tranh chấp xuất hiện ổn định khi demo.

### TH4. Mất Token

Nếu Token bị mất, mọi yêu cầu ghi sẽ chờ vô thời hạn nếu hệ thống không có cơ chế phục hồi. Monitor theo dõi thời điểm cuối cùng Token được quan sát. Timeout chỉ cho biết nghi ngờ mất Token; trong mạng có độ trễ, không thể chỉ dựa vào timeout để chứng minh Token đã biến mất. Quy trình phục hồi phải vô hiệu quyền ghi của thế hệ cũ:

1. Đề xuất tăng `token_epoch` và được ít nhất 3/4 máy xác nhận, lưu bền vững.
2. Các máy xác nhận epoch mới từ chối ghi thuộc epoch cũ; khôi phục trạng thái đã chốt.
3. Sinh đúng một Token mới thuộc epoch đó.
4. Đưa Token mới vào vòng.

Không nên sinh Token mới ngay khi mạng chậm trong vài giây, vì Token cũ có thể vẫn tồn tại và tạo ra hai chủ sở hữu quyền ghi.

### TH5. Token cũ xuất hiện

Token cũ có thể xuất hiện do gói tin bị trễ, máy từng bị cô lập hoạt động lại hoặc một máy khôi phục trạng thái cũ. Mỗi máy chỉ chấp nhận Token có `token_epoch` bằng epoch hiện hành. Token có epoch nhỏ hơn phải bị hủy ngay và không được dùng để xử lý bất kỳ yêu cầu nào.

Cơ chế này chỉ an toàn khi epoch mới được quá bán thống nhất và thao tác ghi cũng được kiểm tra epoch. Một máy bị cô lập có thể chưa biết epoch đã tăng, vì vậy nó không được tự ghi thành công chỉ dựa vào Token cục bộ. Token có epoch lớn hơn thông tin cục bộ cũng phải được xác minh, không tự động được tin cậy.

TH5 đang kiểm tra Token **khác thế hệ**. Nếu muốn kiểm tra hai bản sao Token trong **cùng thế hệ**, cần thêm kiểm tra định danh chuyển Token như TH14; chỉ so sánh epoch không phát hiện được trường hợp này.

### TH6. Máy thường bị sập

Máy đứng trước không thể chỉ suy đoán rằng máy kế tiếp đã sập. Nó phát hiện lỗi thông qua việc không nhận heartbeat hoặc ACK trong thời gian quy định. Sau đó, máy tra danh sách thành viên sống để chọn máy kế tiếp gần nhất trong vòng.

Ví dụ, vòng `1 → 2 → 3 → 4 → 1` sẽ trở thành `1 → 2 → 4 → 1` khi Máy 3 bị loại. Ba máy còn lại đủ 3/4 nên tiếp tục ghi sau khi thống nhất cấu trúc vòng. Nếu Token bị mất đúng lúc chuyển qua Máy 3, hệ thống tiếp tục áp dụng quy trình của TH4.

Máy sập khi đang có thiết bị được người dùng mượn không có nghĩa thiết bị tự động được trả. Trạng thái mượn vẫn được giữ cho tới khi có thao tác trả hợp lệ. TH6 chủ yếu xét máy không giữ Token, không phụ thuộc việc người dùng của máy đó có đang mượn đồ hay không.

### TH7. Máy sập khi giữ Token

Đây là trường hợp khó hơn TH6 vì hệ thống không biết thao tác của Máy 3 đã hoàn tất hay chưa:

- Nếu máy sập trước khi ghi, yêu cầu có thể được xử lý lại.
- Nếu máy sập sau khi ghi nhưng trước khi trả kết quả, xử lý lại có thể tạo dữ liệu trùng.

Vì vậy, mỗi thao tác phải có `operation_id` và được ghi vào nhật ký sao chép. Ba máy còn lại khôi phục nhật ký theo quy tắc commit của giao thức: thao tác đã chốt phải được giữ nguyên; bản ghi chỉ có trên máy sập chưa đủ để chứng minh đã chốt. Thao tác đang dang dở cần được phân giải trước khi cho xử lý yêu cầu tiếp theo. Khi thử lại, dùng đúng `operation_id` cũ để trả lại kết quả đã có thay vì tạo phiếu mới. Chỉ một mã định danh mà không có nhật ký bền vững và quy tắc commit chưa đủ bảo đảm điều này.

Để demo rõ, nên cho tự tắt ở hai điểm: trước khi yêu cầu được chốt và sau khi chốt nhưng trước khi hiện thông báo thành công. Trường hợp sau chứng minh người dùng có thể chưa thấy kết quả nhưng giao dịch vẫn đã có hiệu lực. Không được tự chuyển thiết bị về trạng thái trống chỉ vì máy mượn bị sập.

### TH8. Monitor bị sập

Monitor không được trở thành điểm lỗi duy nhất. Khi các máy không nhận được heartbeat từ Monitor, chúng chạy bầu chọn. Cần công bố rõ thuật toán trước khi demo. Phương án dễ giải thích là Bully Election: máy còn sống có ID lớn nhất thắng.

Ví dụ, ban đầu Máy 4 là Monitor. Khi Máy 4 bị tắt, Máy 3 được ưu tiên vì có ID cao nhất trong ba máy còn sống. Tuy nhiên, ưu tiên ID chỉ là cách chọn ứng viên; quyền Monitor có hiệu lực phải được ít nhất 3/4 máy xác nhận theo nhiệm kỳ. Bully đơn thuần không đủ ngăn hai cụm tự bầu hai Monitor khi phân mảnh.

Monitor mới khôi phục nhật ký, danh sách thành viên và trạng thái Token. Nếu giữ nguyên được quyền sở hữu Token hợp lệ thì không cần sinh thêm; nếu đổi epoch hoặc không xác định được chủ Token thì phục hồi theo TH4. Không được cùng lúc giữ Token cũ và tạo thêm một Token có quyền ghi.

### TH9. Hai máy liên tiếp bị sập

TH9 sử dụng cùng cơ chế phát hiện và nối tắt như TH6, nhưng chứng minh hệ thống có thể vượt qua nhiều nút hỏng liên tiếp. Khi Máy 2 và Máy 3 đều sập, Máy 1 phải tiếp tục dò cho tới khi tìm được Máy 4 thay vì chỉ thử đúng một máy kế tiếp.

Chỉ còn Máy 1 và Máy 4, tức 2/4 máy, nên không đủ ngưỡng ba máy. Dù có thể tạo vòng `1 → 4 → 1`, cả hai phải khóa mượn/trả. Kết nối được với nhau không đồng nghĩa có quyền ghi.

Khi Máy 2 hoặc Máy 3 trở lại, hệ thống có thể đạt 3/4, thống nhất Monitor/epoch và phục hồi nhật ký. Chỉ sau khi các bước này hoàn tất mới mở ghi. Đây là tình huống chứng minh hệ thống ưu tiên tránh cho mượn trùng khi không đủ thông tin.

### TH10. Máy khởi động lại

Máy khởi động lại không được tự nối vào vòng ngay, bởi nó có thể giữ dữ liệu, danh sách thành viên hoặc Token đã lỗi thời. Quy trình gia nhập nên gồm:

1. Gửi `JOIN_REQUEST` tới Monitor.
2. Chuyển sang trạng thái `SYNCING`.
3. Tải trạng thái thiết bị, nhật ký thao tác, epoch và danh sách thành viên mới nhất.
4. Xóa mọi Token cũ đang lưu cục bộ.
5. Được Monitor chèn vào vòng.
6. Chuyển sang trạng thái `ACTIVE`.

Chỉ sau bước cuối máy mới được nhận Token và xử lý yêu cầu. Nếu thử lại yêu cầu chưa nhận kết quả trước khi sập, máy phải dùng `operation_id` cũ. Sau TH6, Máy 3 trở lại sẽ khôi phục vòng `1 → 2 → 3 → 4 → 1`.

### TH11. Máy treo tạm thời

Máy treo không gửi heartbeat nên các máy khác xử lý nó giống một máy đã sập. Điểm nguy hiểm là sau khi hết treo, tiến trình cũ có thể tiếp tục chạy từ đúng vị trí trước đó và tưởng rằng mình vẫn thuộc vòng.

Do đó, khi hoạt động trở lại, máy phải kiểm tra lease, epoch hoặc trạng thái thành viên. Nếu đã bị loại, máy phải bỏ Token và liên kết cũ, chuyển sang `REJOINING` rồi thực hiện lại quy trình của TH10.

Thời gian đóng băng phải dài hơn heartbeat timeout. Chẳng hạn, nếu timeout là 3 giây thì nên đóng băng khoảng 5 giây để kích hoạt nghi ngờ lỗi; thời gian phục hồi thực tế còn phụ thuộc bầu chọn và đồng bộ. Nếu đóng băng Máy 4 đang là Monitor, TH11 cũng đồng thời kích hoạt TH8. Để giải thích riêng lỗi treo máy thường, có thể dùng Máy 2 hoặc Máy 3.

### TH12. Phân mảnh mạng

Nếu hai cụm đều tự tạo Token thì cả hai có thể cùng cho mượn một thiết bị; đây là lỗi split-brain. Để ngăn lỗi này, quyền ghi phải phụ thuộc vào số lượng thành viên:

- Phân mảnh `3–1`, ví dụ `{1, 2, 3}` và `{4}`: nhóm ba máy được ghi sau khi xác nhận quyền và phục hồi; Máy 4 chỉ đọc, kể cả trước đó nó là Monitor hoặc giữ Token.
- Phân mảnh `2–2`, ví dụ `{1, 2}` và `{3, 4}`: cả hai nhóm chỉ đọc vì không bên nào có ít nhất ba máy.

Nếu Token cũ nằm ở cụm thiểu số thì nó cũng không tạo ra quyền ghi. Cụm đa số có thể thống nhất epoch mới và phục hồi một Token hợp lệ. Cần chặn toàn bộ lưu lượng giữa hai nhóm, gồm Token, heartbeat, đồng bộ và bầu chọn; chỉ ngắt hai liên kết trên hình vẽ vòng có thể chưa thật sự tạo phân mảnh nếu các máy vẫn giao tiếp trực tiếp được.

### TH13. Hợp nhất mạng trở lại

Khôi phục kết nối không có nghĩa là hai cụm được ghép vòng ngay. Cụm thiểu số có thể giữ trạng thái cũ nên phải:

1. Dừng xử lý Token cũ.
2. Nhận epoch và danh sách thành viên hiện hành.
3. Tải các thay đổi đã phát sinh trong thời gian bị cô lập.
4. Xác nhận đồng bộ hoàn tất.
5. Gia nhập lại vòng.

Với phân mảnh `3–1`, nhóm ba máy cung cấp lịch sử đã chốt trong thời gian bị cô lập. Với phân mảnh `2–2`, không có nhóm đa số trước đó để làm nguồn mặc định: sau khi kết nối phục hồi, ít nhất ba máy phải cùng khôi phục lịch sử đã chốt và thống nhất nhiệm kỳ mới trước khi mở ghi. Không chọn dữ liệu chỉ theo đồng hồ mới nhất hay ID máy lớn nhất.

Trường hợp này hoàn thiện vòng đời của TH12: phát hiện phân mảnh, duy trì an toàn và phục hồi khi mạng trở lại.

### TH14. Mất gói khi chuyển Token

Giả sử Máy 2 gửi Token cho Máy 3 nhưng không nhận được ACK. Có hai khả năng:

- Gói Token bị mất nên Máy 3 chưa nhận được.
- Máy 3 đã nhận Token nhưng gói ACK bị mất.

Nếu Máy 2 gửi một Token mới mà không kiểm tra, hệ thống có thể xuất hiện Token trùng. Vì vậy, mỗi lần chuyển cần một `transfer_id`. Máy gửi chuyển sang trạng thái đang bàn giao và ngừng sử dụng quyền ghi trước khi máy nhận kích hoạt Token. Khi chưa có ACK, chỉ được gửi lại đúng lần chuyển cũ, không vừa giữ quyền ghi vừa tạo lần chuyển mới. Máy nhận lưu mã này trước khi trả ACK; nếu nhận lại cùng mã, nó chỉ gửi lại ACK chứ không xử lý Token lần hai.

TCP tự truyền lại gói bị mất trong cùng kết nối. Để demo rõ, nút giả lập nên bỏ thông điệp Token/ACK ở tầng ứng dụng hoặc ngắt kết nối ở đúng điểm bàn giao; không nên mô tả một gói TCP mất là lập tức mất Token.

Nếu các máy vẫn không thể xác định chủ sở hữu Token, Monitor sử dụng quy trình phục hồi của TH4: tăng epoch và vô hiệu hóa mọi Token thuộc thế hệ cũ.

## 4. Thứ tự trình bày đề xuất

Để người xem dễ theo dõi, nên chia phần demo thành bốn nhóm:

1. **Hoạt động cơ bản:** TH1 → TH2 → TH3.
2. **Sự cố liên quan đến Token:** TH4 → TH5 → TH14.
3. **Sự cố liên quan đến máy:** TH6 → TH7 → TH8 → TH9.
4. **Phục hồi và phân mảnh mạng:** TH10 → TH11 → TH12 → TH13.

Trong suốt phần demo, giao diện nên hiển thị tối thiểu:

```text
Monitor hiện tại: Máy 4
Máy giữ Token: Máy 2
Token epoch: 4
Thành viên sống: 1, 2, 3, 4
Quorum: 4/4 — Ngưỡng cần: 3 — Cho phép ghi
Vòng hiện tại: 1 → 2 → 3 → 4 → 1
```

Các thông tin này giúp người xem liên hệ hành động trên giao diện với cơ chế phân tán đang diễn ra bên dưới.

Trước mỗi tình huống độc lập, khôi phục đủ bốn máy, mạng thông suốt và dữ liệu mẫu nhất quán. Chỉ giữ lỗi trước đó nếu đang demo chuỗi TH6 → TH10 hoặc TH12 → TH13. Nếu không khôi phục, ví dụ tắt thêm một máy sau TH6, hệ thống sẽ còn 2/4 và phải khóa ghi, làm kết quả khác với tình huống dự kiến.
