# 📡 API Documentation - Ticket System

## 🌐 Base URLs

| Service | URL | Description |
|---------|-----|-------------|
| Booking Service | http://localhost:8081 | Đặt vé |
| Manage Revenue Service | http://localhost:8082 | Quản lý hệ thống |

---

## 🔐 Authentication

### Register
Đăng ký tài khoản mới

**Endpoint**: `POST /api/auth/register`  
**Service**: Manage Revenue (8082)  
**Authentication**: ❌ Not required

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "role": "CUSTOMER"
}
```

**Roles**: `ADMIN`, `DRIVER`, `COLLECTOR`, `CUSTOMER`

**Response** (201 Created):
```json
{
  "code": 201,
  "message": "Register successfully",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

### Login
Đăng nhập vào hệ thống

**Endpoint**: `POST /api/auth/login`  
**Service**: Manage Revenue (8082)  
**Authentication**: ❌ Not required

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Login successfully",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Notes**:
- Access token có hiệu lực 24 giờ
- Session được lưu trong Redis với timeout 30 phút
- Sử dụng token trong header: `Authorization: Bearer <token>`

---

### Update Password
Đổi mật khẩu

**Endpoint**: `PUT /api/auth/update-password`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Headers**:
```
Authorization: Bearer <your-access-token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "oldPassword": "oldpassword123",
  "password": "newpassword123"
}
```

**Response** (201 Created):
```json
{
  "code": 201,
  "message": "Update Password successfully",
  "data": null
}
```

---

## 🎫 Booking APIs

### Create Booking
Đặt vé mới (gửi vào Kafka)

**Endpoint**: `POST /api/booking`  
**Service**: Booking (8081)  
**Authentication**: ✅ Required

**Headers**:
```
Authorization: Bearer <your-access-token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "tripId": 1,
  "customerEmail": "customer@example.com",
  "seatNumber": 15,
  "price": 150000,
  "status": "BOOKED"
}
```

**Status Values**: `NOT_BOOKED`, `BOOKED`, `PAID`, `CANCELLED`

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Booking created successfully",
  "data": null
}
```

**Notes**:
- Booking được gửi vào Kafka topic `order-events`
- Consumer ở Manage Revenue Service sẽ xử lý
- Email xác nhận sẽ được gửi tự động

---

## 👥 User Management APIs

### Get All Users
Lấy danh sách tất cả users

**Endpoint**: `GET /api/users`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Query Parameters**:
- `page` (optional): Số trang (default: 0)
- `size` (optional): Kích thước trang (default: 20)
- `role` (optional): Filter theo role

**Example**: `GET /api/users?page=0&size=10&role=CUSTOMER`

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "content": [
      {
        "id": 1,
        "email": "user@example.com",
        "role": "CUSTOMER",
        "isActive": true,
        "createdAt": "2026-04-01T10:00:00",
        "updatedAt": "2026-04-01T10:00:00"
      }
    ],
    "totalElements": 50,
    "totalPages": 5,
    "size": 10,
    "number": 0
  }
}
```

---

### Get User by ID
Lấy thông tin user theo ID

**Endpoint**: `GET /api/users/{id}`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Example**: `GET /api/users/1`

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "role": "CUSTOMER",
    "isActive": true,
    "driverStatus": null,
    "userStatus": "ACTIVE",
    "createdAt": "2026-04-01T10:00:00",
    "updatedAt": "2026-04-01T10:00:00"
  }
}
```

---

### Create User
Tạo user mới (ADMIN only)

**Endpoint**: `POST /api/users`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "password": "password123",
  "role": "DRIVER",
  "driverStatus": "AVAILABLE"
}
```

---

### Update User
Cập nhật thông tin user

**Endpoint**: `PUT /api/users/{id}`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Request Body**:
```json
{
  "email": "updated@example.com",
  "role": "COLLECTOR",
  "isActive": true
}
```

---

### Delete User
Xóa user (soft delete)

**Endpoint**: `DELETE /api/users/{id}`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "User deleted successfully",
  "data": null
}
```

---

## 🛣️ Route Management APIs

### Get All Routes
Lấy danh sách tuyến đường

**Endpoint**: `GET /api/routes`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Query Parameters**:
- `status` (optional): `ACTIVE`, `INACTIVE`

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "routeName": "Hà Nội - Hải Phòng",
      "startPoint": "Hà Nội",
      "endPoint": "Hải Phòng",
      "distanceKm": 120.5,
      "status": "ACTIVE",
      "createdAt": "2026-04-01T10:00:00"
    }
  ]
}
```

---

### Get Route by ID
Lấy thông tin tuyến đường theo ID

**Endpoint**: `GET /api/routes/{id}`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

---

### Create Route
Tạo tuyến đường mới

**Endpoint**: `POST /api/routes`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Request Body**:
```json
{
  "routeName": "Hà Nội - Đà Nẵng",
  "startPoint": "Hà Nội",
  "endPoint": "Đà Nẵng",
  "distanceKm": 765.0,
  "status": "ACTIVE"
}
```

---

### Update Route
Cập nhật tuyến đường

**Endpoint**: `PUT /api/routes/{id}`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

---

### Delete Route
Xóa tuyến đường

**Endpoint**: `DELETE /api/routes/{id}`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

---

## 🚌 Bus Management APIs

### Get All Buses
Lấy danh sách xe bus

**Endpoint**: `GET /api/buses`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "busNumber": "BUS-001",
      "licensePlate": "29A-12345",
      "capacity": 40,
      "status": "AVAILABLE",
      "createdAt": "2026-04-01T10:00:00"
    }
  ]
}
```

**Status Values**: `AVAILABLE`, `IN_USE`, `MAINTENANCE`

---

### Create Bus
Thêm xe bus mới

**Endpoint**: `POST /api/buses`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Request Body**:
```json
{
  "busNumber": "BUS-002",
  "licensePlate": "30B-67890",
  "capacity": 45,
  "status": "AVAILABLE"
}
```

---

### Update Bus
Cập nhật thông tin xe

**Endpoint**: `PUT /api/buses/{id}`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

---

### Delete Bus
Xóa xe bus

**Endpoint**: `DELETE /api/buses/{id}`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

---

## 🚗 Trip Management APIs

### Get All Trips
Lấy danh sách chuyến xe

**Endpoint**: `GET /api/trips`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Query Parameters**:
- `status` (optional): `SCHEDULED`, `ONGOING`, `COMPLETED`, `CANCELLED`
- `routeId` (optional): Filter theo route
- `driverId` (optional): Filter theo driver
- `date` (optional): Filter theo ngày (format: yyyy-MM-dd)

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "route": {
        "id": 1,
        "routeName": "Hà Nội - Hải Phòng"
      },
      "bus": {
        "id": 1,
        "busNumber": "BUS-001"
      },
      "driver": {
        "id": 2,
        "email": "driver@example.com"
      },
      "departureTime": "2026-04-10T08:00:00",
      "arrivalTime": "2026-04-10T10:30:00",
      "status": "SCHEDULED",
      "revenue": 0.00
    }
  ]
}
```

---

### Create Trip
Tạo chuyến xe mới

**Endpoint**: `POST /api/trips`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Request Body**:
```json
{
  "routeId": 1,
  "busId": 1,
  "driverId": 2,
  "departureTime": "2026-04-10T08:00:00",
  "arrivalTime": "2026-04-10T10:30:00",
  "status": "SCHEDULED"
}
```

---

### Update Trip
Cập nhật chuyến xe

**Endpoint**: `PUT /api/trips/{id}`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

---

### Complete Trip
Đánh dấu chuyến xe hoàn thành

**Endpoint**: `PUT /api/trips/{id}/complete`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Response**: Tự động tính toán doanh thu từ các vé đã bán

---

## 🎫 Ticket Management APIs

### Get All Tickets
Lấy danh sách vé

**Endpoint**: `GET /api/tickets`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Query Parameters**:
- `tripId` (optional): Filter theo chuyến xe
- `customerId` (optional): Filter theo khách hàng
- `status` (optional): `NOT_BOOKED`, `BOOKED`, `PAID`, `CANCELLED`

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "trip": {
        "id": 1,
        "departureTime": "2026-04-10T08:00:00"
      },
      "customer": {
        "id": 3,
        "email": "customer@example.com"
      },
      "seller": {
        "id": 4,
        "email": "seller@example.com"
      },
      "seatNumber": 15,
      "price": 150000.00,
      "statusTicket": "BOOKED",
      "issuedAt": "2026-04-09T14:30:00"
    }
  ]
}
```

---

### Get My Tickets
Lấy danh sách vé của user hiện tại

**Endpoint**: `GET /api/tickets/my-tickets`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

---

### Create Ticket
Tạo vé mới

**Endpoint**: `POST /api/tickets`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Request Body**:
```json
{
  "tripId": 1,
  "customerId": 3,
  "sellerId": 4,
  "seatNumber": 15,
  "price": 150000.00,
  "statusTicket": "BOOKED"
}
```

---

### Cancel Ticket
Hủy vé

**Endpoint**: `PUT /api/tickets/{id}/cancel`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

---

## 💰 Revenue Management APIs

### Get Revenue Report
Báo cáo doanh thu tổng quan

**Endpoint**: `GET /api/revenue/report`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Query Parameters**:
- `startDate`: yyyy-MM-dd
- `endDate`: yyyy-MM-dd

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "totalRevenue": 15000000.00,
    "totalTrips": 50,
    "totalTickets": 1500,
    "averageRevenuePerTrip": 300000.00,
    "period": {
      "startDate": "2026-04-01",
      "endDate": "2026-04-09"
    }
  }
}
```

---

### Revenue by Route
Doanh thu theo tuyến đường

**Endpoint**: `GET /api/revenue/by-route`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Query Parameters**:
- `startDate`: yyyy-MM-dd (optional)
- `endDate`: yyyy-MM-dd (optional)

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "routeId": 1,
      "routeName": "Hà Nội - Hải Phòng",
      "totalRevenue": 5000000.00,
      "totalTrips": 20,
      "totalTickets": 600
    }
  ]
}
```

---

### Revenue by Date
Doanh thu theo ngày

**Endpoint**: `GET /api/revenue/by-date`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "date": "2026-04-09",
      "totalRevenue": 1200000.00,
      "totalTrips": 5,
      "totalTickets": 150
    }
  ]
}
```

---

### Top Customers
Top khách hàng theo doanh thu

**Endpoint**: `GET /api/revenue/top-customers`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Query Parameters**:
- `limit` (optional): Số lượng (default: 10)

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "customerId": 3,
      "customerEmail": "customer@example.com",
      "totalSpent": 2500000.00,
      "totalTrips": 15,
      "loyaltyPoints": 250
    }
  ]
}
```

---

## ⭐ Loyalty Points APIs

### Get My Points
Xem điểm thưởng của mình

**Endpoint**: `GET /api/loyalty-points`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "userId": 3,
    "totalPoints": 250,
    "transactions": [
      {
        "id": 1,
        "points": 50,
        "transactionType": "EARN",
        "description": "Đặt vé trip #1",
        "createdAt": "2026-04-09T10:00:00"
      }
    ]
  }
}
```

---

### Earn Points
Tích điểm (tự động khi đặt vé)

**Endpoint**: `POST /api/loyalty-points/earn`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Request Body**:
```json
{
  "userId": 3,
  "points": 50,
  "description": "Đặt vé trip #1"
}
```

---

### Redeem Points
Đổi điểm lấy quà

**Endpoint**: `POST /api/loyalty-points/redeem`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

**Request Body**:
```json
{
  "userId": 3,
  "points": 100,
  "rewardId": 1
}
```

---

### Get Loyalty Rewards
Xem danh sách phần thưởng

**Endpoint**: `GET /api/loyalty-rewards`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required

---

## 💵 Salary Management APIs

### Get Salaries
Lấy danh sách lương

**Endpoint**: `GET /api/salary`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Query Parameters**:
- `userId` (optional): Filter theo user
- `month` (optional): Tháng (1-12)
- `year` (optional): Năm

---

### Calculate Salary
Tính lương tự động

**Endpoint**: `POST /api/salary/calculate`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Request Body**:
```json
{
  "userId": 2,
  "month": 4,
  "year": 2026
}
```

---

### Get Base Salaries
Xem mức lương cơ bản

**Endpoint**: `GET /api/base-salary`  
**Service**: Manage Revenue (8082)  
**Authentication**: ✅ Required (ADMIN)

**Response** (200 OK):
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "role": "DRIVER",
      "baseSalary": 8000000.00,
      "status": "ACTIVE"
    }
  ]
}
```

---

## 🧪 Testing APIs

### Postman Collection
Import file Postman collection (nếu có) để test APIs nhanh hơn.

### cURL Examples

**Login:**
```bash
curl -X POST http://localhost:8082/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**Get Users (with token):**
```bash
curl -X GET http://localhost:8082/api/users \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Create Route:**
```bash
curl -X POST http://localhost:8082/api/routes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "routeName": "Hà Nội - Hải Phòng",
    "startPoint": "Hà Nội",
    "endPoint": "Hải Phòng",
    "distanceKm": 120.5,
    "status": "ACTIVE"
  }'
```

---

## 📝 Response Format

### Success Response
```json
{
  "code": 200,
  "message": "Success message",
  "data": { ... }
}
```

### Error Response
```json
{
  "code": 400,
  "message": "Error message",
  "data": null
}
```

### HTTP Status Codes
- `200 OK` - Thành công
- `201 Created` - Tạo mới thành công
- `400 Bad Request` - Request không hợp lệ
- `401 Unauthorized` - Chưa đăng nhập
- `403 Forbidden` - Không có quyền
- `404 Not Found` - Không tìm thấy
- `500 Internal Server Error` - Lỗi server

---

## 🔒 Security Headers

Tất cả authenticated requests cần header:
```
Authorization: Bearer <access-token>
Content-Type: application/json
```

---

**Last Updated**: April 9, 2026  
**API Version**: 1.0.0

