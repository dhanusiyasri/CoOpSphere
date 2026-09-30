# Attendance-04 — Low Attendance Alerts

## Purpose
Adds operational low-attendance detection on top of Attendance-03 reports. No new database tables or migration are required.

## Manager view
Manager roles (`NCCT_ADMIN`, `INSTITUTE_ADMIN`, `TRAINER`) can use the Attendance Reports screen to check trainees below a configurable threshold (default 75%).

Filters reuse the Attendance-03 report filters:
- From date
- To date
- Batch ID
- Attendance threshold (0–100%)

The API scopes results by role in the same way as Attendance-03:
- Trainer: assigned batches
- Institute admin: programmes belonging to their institution
- NCCT admin: all visible attendance data

## API
- `GET /api/v1/attendance/alerts/low-attendance`
- Optional query parameters: `threshold`, `from_date`, `to_date`, `batch_id`

## UI
The Reports & analytics screen now includes a **Low-attendance alerts** panel with trainee, batch, session count, present/late/absent counts and attendance rate.

## Migration
No migration is needed. The alert is calculated from existing attendance sessions, attendance records and active enrollments.
