# ERP-09 — Training Logistics & Hostel

Adds batch-level logistics planning for residential training: hostel, meals, transport and coordinator details, plus room/bed allocation for active enrolled trainees.

## Endpoints
- GET /api/v1/training/logistics/plans
- POST /api/v1/training/logistics/plans
- GET /api/v1/training/logistics/allocations
- POST /api/v1/training/logistics/allocations

## Migration
- 0017_training_logistics

## Role rules
- NCCT_ADMIN, INSTITUTE_ADMIN, TRAINER manage logistics within their existing batch scope.
- TRAINEE sees logistics for active enrollments only.
