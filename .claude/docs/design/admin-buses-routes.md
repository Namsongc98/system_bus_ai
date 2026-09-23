# Màn hình: Quản lý Xe & Tuyến đường

> Figma: node-id `2:2475` (tên frame: "Buses & Routes") — file "Ticket-Buses" (`fileKey=QgeicQW2IuhLakGxpsQnr1`)
> Nhóm: Admin Terminal
> Slug: `admin-buses-routes`

## 1. Tổng quan

1 màn hình gộp 2 domain: cột trái quản lý **Fleet (xe)**, cột phải quản lý **Routes Network (tuyến
đường)**, có mini-map trực quan hoá mạng lưới tuyến ở dưới.

## 2. Basic Design

- `Section - Left Column: Buses Fleet`: heading + nút "Add" + `Bus Fleet Grid` (card xe, mỗi card có
  driver gắn kèm, nút hành động) + `Add New Card Skeleton` (card rỗng để thêm mới).
- `Section - Right Column: Routes Network`: heading + nút "Add" + danh sách `Route Card` (mỗi card
  có input tìm kiếm/label riêng — cần xem lại, có thể là inline-edit).
- `Network Visualization Mini-Map`: bản đồ tuyến, không thao tác trực tiếp (chỉ xem).

## 3. Detail Design

| Khối | Field hiển thị | Map với entity |
|---|---|---|
| Bus Card | biển số, sức chứa, trạng thái, driver gắn kèm | `Buses.plateNumber`, `.capacity`, `.status` (`BusStatus`: ACTIVE/INACTIVE/PENDING), driver là quan hệ riêng — **chưa thấy field liên kết Bus↔Driver ở entity `Buses`/`Trip`** (driver hiện chỉ gắn ở `Trip.driver`, không gắn cố định vào `Buses`) |
| Route Card | tên tuyến, điểm đầu/cuối, khoảng cách, trạng thái | `Route.routeName`, `.startPoint`, `.endPoint`, `.distanceKm`, `.status` (`RouteStatus`: ACTIVE/INACTIVE) |
| Nút "Add" (Bus/Route) | mở modal tương ứng | xem `admin-create-bus-modal.md` / `admin-create-route-modal.md` |
| Nút hành động trên card | sửa/xoá (icon button) | sửa → mở modal edit (`PUT`); xoá → xem `admin-delete-confirmation.md` |

**States:** loading grid, empty state (chưa có xe/tuyến nào), lỗi tải danh sách, phân trang (Bus có
`Page` từ backend, Route hiện chưa rõ vì không có API list).

## 4. Business Logic

1. Load trang → gọi `GET /api/bus?page=&size=` để lấy danh sách xe (đã hỗ trợ phân trang).
2. Load danh sách tuyến → **không có API**, cần bổ sung `GET /api/route`.
3. Sửa xe → `PUT /api/bus/{busId}`. Sửa tuyến → `PUT /api/route/{routeId}`.
4. Xoá xe/tuyến → **chưa có API `DELETE`** cho cả `BusController` lẫn `RouteController`.
5. Card driver hiển thị trên Bus Card — cần làm rõ nguồn dữ liệu vì `Buses` entity không có field
   driver; có thể lấy gián tiếp qua `Trip` gần nhất/hiện tại của xe đó, cần xác nhận nghiệp vụ.

## 5. API

| Method | Path | Trạng thái | Request/Response | Nguồn |
|---|---|---|---|---|
| GET | `/api/bus?page=&size=` | Đã có | trả `Page<Buses>` | `BusController.java:24` |
| POST | `/api/bus` | Đã có | `BusRequest` (`plateNumber`, `capacity`, `status`) | `BusController.java:38` |
| PUT | `/api/bus/{busId}` | Đã có | `BusRequest` | `BusController.java:44` |
| DELETE | `/api/bus/{busId}` | **Cần tạo mới** | — | — |
| POST | `/api/route` | Đã có | `RouteRequestDto` (`routeName`, `startPoint`, `endPoint`, `distanceKm`, `status`) | `RouteController.java:18` |
| PUT | `/api/route/{routeId}` | Đã có | `RouteRequestDto` | `RouteController.java:25` |
| GET | `/api/route?page=&size=` | **Cần tạo mới** | — | — |
| DELETE | `/api/route/{routeId}` | **Cần tạo mới** | — | — |

## 6. Requirements

- [ ] (Blocking) Tạo `GET /api/route` (list, nên có phân trang giống `GET /api/bus`) trước khi
      implement cột phải màn hình này.
- [ ] (Blocking) Tạo `DELETE /api/bus/{busId}` và `DELETE /api/route/{routeId}` để phục vụ nút xoá.
- [ ] Làm rõ nguồn dữ liệu driver hiển thị trên Bus Card (không có quan hệ trực tiếp Bus↔Driver ở
      entity hiện tại).
- [ ] Validate không cho xoá Bus/Route đang được gán cho Trip `SCHEDULED`/`ONGOING` (ràng buộc toàn
      vẹn dữ liệu — cần backend kiểm tra, không chỉ chặn ở FE).
- [ ] (TODO/needs confirmation) Route Card trong Figma có ô input — xác nhận đây là search/filter
      hay inline-edit tên tuyến.
