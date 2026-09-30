# Attendance-01 — Session & Attendance Register

This slice adds batch-linked training sessions and persisted trainee attendance.

## Scope
- Create scheduled/open/closed attendance sessions for a batch.
- Generate a unique attendance access code.
- Generate a QR image containing the attendance payload.
- View the batch trainee roster.
- Mark PRESENT, LATE or ABSENT manually.
- Trainees can check in with the access code; the stored method is `QR` to keep the data model ready for camera scanning.

Camera-based QR scanning is intentionally not included in this slice. The next attendance slice can add browser camera scanning without changing the database model.
