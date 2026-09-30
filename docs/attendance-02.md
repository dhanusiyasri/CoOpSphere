# Attendance-02

Adds cross-browser QR camera scanning for trainees using the open-source `html5-qrcode` library, while retaining manual access-code check-in as a fallback. Adds a manager attendance summary with present, late, absent and attendance-rate counts. No database migration is required.

The scanner requests camera permission only after the trainee clicks **Scan QR with camera**. It prefers a rear/environment camera when the browser exposes camera labels, and otherwise uses the first available camera.

Camera access works only when the browser/device permits camera access. `http://localhost:5173` is treated as a secure context by modern browsers; deployed environments should use HTTPS. If camera access is unavailable or denied, the manual attendance code remains available.

## Frontend dependency

The frontend now declares:

```text
html5-qrcode 2.3.8
```

Run `npm install` after applying this slice so the dependency is installed locally.
