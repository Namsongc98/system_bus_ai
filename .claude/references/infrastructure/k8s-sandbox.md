# K8s Sandbox

Index: [README.md](README.md) · Runbook: `ticket-system/Infrastructure/k8s-sandbox/README.md`

## Vai trò

Bài tập Kubernetes trên **VM2 k3s riêng** — thực hành Pod, Deployment, Service, probe. Không nằm trong
luồng dev hay prod, không nối MySQL/Kafka/Redis thật (tránh tạo consumer group đọc trùng dữ liệu prod).
Chỉ dùng chung image CI build.

## File `booking-deployment.yaml`

| Đối tượng | Tên | Nội dung |
|---|---|---|
| Deployment | `booking-replica` | 1 replica, image `ghcr.io/changeme/ticket-system-booking_ticket:latest`, cổng 8081, `limits.memory 500Mi` |
| Service | `booking-replica-svc` | ClusterIP, 80 → 8081, selector `app: booking-replica` |

readinessProbe: `httpGet /actuator/health:8081`, `initialDelaySeconds: 15`.

## Chạy

```bash
curl -sfL https://get.k3s.io | sh -                  # VM2, 1 lần
kubectl apply -f booking-deployment.yaml
kubectl get pods -l app=booking-replica
kubectl describe pod -l app=booking-replica           # sự kiện probe, OOMKilled
kubectl port-forward svc/booking-replica-svc 8081:80
kubectl delete -f booking-deployment.yaml
```

## Lưu ý

- `changeme` là placeholder owner GitHub; image private cần `imagePullSecrets`.
- Không có DB/Kafka/Redis → Spring có thể không khởi động hoặc readiness luôn `DOWN`; không có env/secret nào được truyền.
- B29e: probe đang dùng `/actuator/health` (gồm mail) thay vì `/actuator/health/readiness` như Kong;
  trong sandbox không hạ tầng, `/actuator/health/liveness` hợp lý hơn.
- `DEPLOYMENT.md` cài thêm ingress-nginx nhưng file chưa có `Ingress`.
