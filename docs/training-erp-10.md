# ERP-10 — Training Evaluation & Feedback

Proposed next vertical slice for the NCCT cooperative ecosystem. This slice adds session-level trainee feedback and manager-facing aggregated evaluation insights, reusing the existing Training Schedule and Enrollment records.

## Trainee
- View scheduled training sessions for active batches.
- Submit one feedback record per scheduled session.
- Rate content, trainer, venue/delivery and overall experience from 1–5.
- Add optional comments.
- Prevent duplicate submissions for the same session.

## Managers
- View aggregated session ratings.
- Filter by batch.
- See response count and average ratings without exposing individual comments in the summary.

## API
- GET `/api/v1/training/evaluations`
- POST `/api/v1/training/evaluations`
- GET `/api/v1/training/evaluations/summary`

## Migration
- `0018_training_evaluation`
