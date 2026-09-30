# ERP-08 — Timetable & Training Session Scheduling

This slice adds a central timetable for training batches and links scheduled sessions to the existing Attendance module.

## Features
- Managers create dated training sessions inside a batch's start/end dates.
- Optional course, module and trainer assignment.
- Venue, delivery mode, topic, status and notes.
- Trainees see schedules only for their active enrollments.
- Institute administrators are restricted to their institution.
- Trainers see/manage only their assigned batches.
- A manager can create the matching attendance session directly from a scheduled session.
- Existing attendance QR/check-in workflows remain unchanged.

## Endpoints
- `GET /api/v1/training/schedules`
- `POST /api/v1/training/schedules`
- `POST /api/v1/training/schedules/{schedule_id}/attendance`

## Migration
- `0016_training_scheduling`

## Demo
The seed adds two timetable entries for the demo batch when no schedules exist yet.
