from datetime import date, datetime, timezone
import base64
import io
import secrets

import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.training.models import Enrollment, TrainingBatch, TrainingProgramme
from app.users.models import User
from app.attendance.models import AttendanceRecord, AttendanceSession
from app.attendance.schemas import (
    AttendanceCheckIn,
    AttendanceQrResponse,
    AttendanceRecordResponse,
    AttendanceRecordUpdate,
    AttendanceSessionCreate,
    AttendanceSessionResponse,
    AttendanceReportResponse,
    AttendanceReportSummary,
    AttendanceReportBatch,
    AttendanceReportSession,
    AttendanceReportTrainee,
    LowAttendanceAlert,
    LowAttendanceAlertResponse,
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])
MANAGERS = require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER")


def _code(db: Session) -> str:
    for _ in range(20):
        value = secrets.token_hex(4).upper()
        if not db.scalar(select(AttendanceSession).where(AttendanceSession.access_code == value)):
            return value
    raise HTTPException(status_code=500, detail="Could not generate attendance access code")


def _session(db: Session, session_id: int) -> AttendanceSession:
    obj = db.get(AttendanceSession, session_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    return obj


def _roster_row(record: AttendanceRecord, trainee: User) -> AttendanceRecordResponse:
    return AttendanceRecordResponse(
        id=record.id, session_id=record.session_id, trainee_id=record.trainee_id,
        status=record.status, method=record.method, check_in_at=record.check_in_at,
        marked_by_id=record.marked_by_id, remarks=record.remarks,
        trainee_name=trainee.full_name, trainee_email=trainee.email,
    )


def _rate(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 1) if denominator else 0.0


def _report_sessions(
    db: Session,
    current_user: User,
    from_date: date | None,
    to_date: date | None,
    batch_id: int | None,
    trainee_id: int | None = None,
):
    query = (
        select(AttendanceSession, TrainingBatch)
        .join(TrainingBatch, TrainingBatch.id == AttendanceSession.batch_id)
        .order_by(AttendanceSession.session_date.desc(), AttendanceSession.start_time.desc())
    )
    if from_date:
        query = query.where(AttendanceSession.session_date >= from_date)
    if to_date:
        query = query.where(AttendanceSession.session_date <= to_date)
    if batch_id:
        query = query.where(AttendanceSession.batch_id == batch_id)
    if current_user.role == "TRAINER":
        query = query.where(TrainingBatch.trainer_id == current_user.id)
    elif current_user.role == "INSTITUTE_ADMIN":
        query = query.join(TrainingProgramme, TrainingProgramme.id == TrainingBatch.programme_id).where(
            TrainingProgramme.institution_id == current_user.institution_id
        )
    if trainee_id is not None:
        query = query.join(
            Enrollment,
            (Enrollment.batch_id == AttendanceSession.batch_id) & (Enrollment.trainee_id == trainee_id),
        ).where(Enrollment.status == "ACTIVE")
    return db.execute(query).all()


@router.get("/reports", response_model=AttendanceReportResponse)
def attendance_report(
    from_date: date | None = None,
    to_date: date | None = None,
    batch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(MANAGERS),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be on or before to_date")

    rows = _report_sessions(db, current_user, from_date, to_date, batch_id)
    session_ids = [session.id for session, _batch in rows]
    batch_ids = sorted({session.batch_id for session, _batch in rows})

    enrollments_by_batch: dict[int, list[Enrollment]] = {}
    if batch_ids:
        enrollments = db.scalars(
            select(Enrollment).where(Enrollment.batch_id.in_(batch_ids), Enrollment.status == "ACTIVE")
        ).all()
        for enrollment in enrollments:
            enrollments_by_batch.setdefault(enrollment.batch_id, []).append(enrollment)

    records = []
    if session_ids:
        records = db.scalars(
            select(AttendanceRecord).where(AttendanceRecord.session_id.in_(session_ids))
        ).all()
    record_by_key = {(r.session_id, r.trainee_id): r for r in records}

    session_items: list[AttendanceReportSession] = []
    batch_acc: dict[int, dict] = {}
    trainee_acc: dict[int, dict] = {}
    qr_checkins = 0
    manual_marks = 0

    for session, batch in rows:
        roster = enrollments_by_batch.get(batch.id, [])
        counts = {"PRESENT": 0, "LATE": 0, "ABSENT": 0, "EXCUSED": 0}
        for enrollment in roster:
            record = record_by_key.get((session.id, enrollment.trainee_id))
            status_value = record.status if record else "ABSENT"
            if status_value not in counts:
                status_value = "ABSENT"
            counts[status_value] += 1
            if record:
                if record.method == "QR":
                    qr_checkins += 1
                if record.method == "MANUAL":
                    manual_marks += 1

            trainee = db.get(User, enrollment.trainee_id)
            if trainee:
                acc = trainee_acc.setdefault(
                    trainee.id,
                    {
                        "trainee_id": trainee.id,
                        "trainee_name": trainee.full_name,
                        "trainee_email": trainee.email,
                        "total_sessions": 0,
                        "present": 0,
                        "late": 0,
                        "absent": 0,
                        "excused": 0,
                        "last_check_in_at": None,
                    },
                )
                acc["total_sessions"] += 1
                acc[status_value.lower()] += 1
                if record and record.check_in_at and (
                    acc["last_check_in_at"] is None or record.check_in_at > acc["last_check_in_at"]
                ):
                    acc["last_check_in_at"] = record.check_in_at

        attendance_slots = len(roster)
        attended = counts["PRESENT"] + counts["LATE"]
        session_items.append(
            AttendanceReportSession(
                session_id=session.id,
                batch_id=batch.id,
                batch_code=batch.batch_code,
                session_date=session.session_date,
                start_time=session.start_time,
                end_time=session.end_time,
                topic=session.topic,
                status=session.status,
                roster_count=attendance_slots,
                present=counts["PRESENT"],
                late=counts["LATE"],
                absent=counts["ABSENT"],
                excused=counts["EXCUSED"],
                attendance_rate=_rate(attended, attendance_slots),
            )
        )
        acc = batch_acc.setdefault(
            batch.id,
            {
                "batch_id": batch.id,
                "batch_code": batch.batch_code,
                "total_sessions": 0,
                "enrolled_trainees": len(roster),
                "attendance_slots": 0,
                "present": 0,
                "late": 0,
                "absent": 0,
                "excused": 0,
            },
        )
        acc["total_sessions"] += 1
        acc["enrolled_trainees"] = max(acc["enrolled_trainees"], len(roster))
        acc["attendance_slots"] += attendance_slots
        for key in ("present", "late", "absent", "excused"):
            acc[key] += counts[key.upper()]

    total_sessions = len(session_items)
    enrolled_trainees = sum(x["enrolled_trainees"] for x in batch_acc.values())
    attendance_slots = sum(x["attendance_slots"] for x in batch_acc.values())
    present = sum(x["present"] for x in batch_acc.values())
    late = sum(x["late"] for x in batch_acc.values())
    absent = sum(x["absent"] for x in batch_acc.values())
    excused = sum(x["excused"] for x in batch_acc.values())

    return AttendanceReportResponse(
        from_date=from_date,
        to_date=to_date,
        batch_id=batch_id,
        summary=AttendanceReportSummary(
            total_sessions=total_sessions,
            enrolled_trainees=enrolled_trainees,
            attendance_slots=attendance_slots,
            present=present,
            late=late,
            absent=absent,
            excused=excused,
            attendance_rate=_rate(present + late, attendance_slots),
            qr_checkins=qr_checkins,
            manual_marks=manual_marks,
            exceptions=late + absent,
        ),
        batches=[
            AttendanceReportBatch(**item, attendance_rate=_rate(item["present"] + item["late"], item["attendance_slots"]))
            for item in batch_acc.values()
        ],
        sessions=session_items,
        trainees=[
            AttendanceReportTrainee(
                **item,
                attendance_rate=_rate(item["present"] + item["late"], item["total_sessions"]),
            )
            for item in sorted(trainee_acc.values(), key=lambda x: x["trainee_name"].lower())
        ],
    )


@router.get("/reports/my", response_model=AttendanceReportResponse)
def my_attendance_report(
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "TRAINEE":
        raise HTTPException(status_code=403, detail="Only trainees can access their personal attendance report")
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be on or before to_date")

    rows = _report_sessions(db, current_user, from_date, to_date, None, current_user.id)
    session_ids = [session.id for session, _batch in rows]
    records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id.in_(session_ids), AttendanceRecord.trainee_id == current_user.id)).all() if session_ids else []
    record_by_session = {r.session_id: r for r in records}

    session_items = []
    present = late = absent = excused = 0
    qr_checkins = manual_marks = 0
    for session, batch in rows:
        record = record_by_session.get(session.id)
        status_value = record.status if record else "ABSENT"
        if status_value == "PRESENT": present += 1
        elif status_value == "LATE": late += 1
        elif status_value == "EXCUSED": excused += 1
        else: absent += 1
        if record and record.method == "QR": qr_checkins += 1
        if record and record.method == "MANUAL": manual_marks += 1
        session_items.append(
            AttendanceReportSession(
                session_id=session.id,
                batch_id=batch.id,
                batch_code=batch.batch_code,
                session_date=session.session_date,
                start_time=session.start_time,
                end_time=session.end_time,
                topic=session.topic,
                status=session.status,
                roster_count=1,
                present=1 if status_value == "PRESENT" else 0,
                late=1 if status_value == "LATE" else 0,
                absent=1 if status_value == "ABSENT" else 0,
                excused=1 if status_value == "EXCUSED" else 0,
                attendance_rate=100.0 if status_value in {"PRESENT", "LATE"} else 0.0,
            )
        )

    total_sessions = len(session_items)
    last_check_in = max((r.check_in_at for r in records if r.check_in_at), default=None)
    trainee_item = AttendanceReportTrainee(
        trainee_id=current_user.id,
        trainee_name=current_user.full_name,
        trainee_email=current_user.email,
        total_sessions=total_sessions,
        present=present,
        late=late,
        absent=absent,
        excused=excused,
        attendance_rate=_rate(present + late, total_sessions),
        last_check_in_at=last_check_in,
    )
    my_batches = []
    for batch in {b.id: b for _s, b in rows}.values():
        total = sum(1 for _s, b in rows if b.id == batch.id)
        p_count = sum(1 for s, b in rows if b.id == batch.id and record_by_session.get(s.id) and record_by_session[s.id].status == "PRESENT")
        l_count = sum(1 for s, b in rows if b.id == batch.id and record_by_session.get(s.id) and record_by_session[s.id].status == "LATE")
        a_count = sum(1 for s, b in rows if b.id == batch.id and (not record_by_session.get(s.id) or record_by_session[s.id].status == "ABSENT"))
        e_count = sum(1 for s, b in rows if b.id == batch.id and record_by_session.get(s.id) and record_by_session[s.id].status == "EXCUSED")
        my_batches.append(AttendanceReportBatch(batch_id=batch.id,batch_code=batch.batch_code,total_sessions=total,enrolled_trainees=1,attendance_slots=total,present=p_count,late=l_count,absent=a_count,excused=e_count,attendance_rate=_rate(p_count+l_count,total)))

    return AttendanceReportResponse(
        from_date=from_date,
        to_date=to_date,
        batch_id=None,
        summary=AttendanceReportSummary(
            total_sessions=total_sessions,
            enrolled_trainees=1 if total_sessions else 0,
            attendance_slots=total_sessions,
            present=present,
            late=late,
            absent=absent,
            excused=excused,
            attendance_rate=_rate(present + late, total_sessions),
            qr_checkins=qr_checkins,
            manual_marks=manual_marks,
            exceptions=late + absent,
        ),
        batches=my_batches,
        sessions=session_items,
        trainees=[trainee_item],
    )


@router.get("/alerts/low-attendance", response_model=LowAttendanceAlertResponse)
def low_attendance_alerts(
    threshold: float = 75.0,
    from_date: date | None = None,
    to_date: date | None = None,
    batch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(MANAGERS),
):
    if threshold < 0 or threshold > 100:
        raise HTTPException(status_code=400, detail="threshold must be between 0 and 100")
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be on or before to_date")

    rows = _report_sessions(db, current_user, from_date, to_date, batch_id)
    session_ids = [session.id for session, _batch in rows]
    batch_ids = sorted({session.batch_id for session, _batch in rows})
    if not session_ids:
        return LowAttendanceAlertResponse(threshold=threshold, alerts=[])

    enrollments = db.scalars(
        select(Enrollment).where(Enrollment.batch_id.in_(batch_ids), Enrollment.status == "ACTIVE")
    ).all()
    enrollment_by_batch: dict[int, list[Enrollment]] = {}
    for enrollment in enrollments:
        enrollment_by_batch.setdefault(enrollment.batch_id, []).append(enrollment)

    records = db.scalars(
        select(AttendanceRecord).where(AttendanceRecord.session_id.in_(session_ids))
    ).all()
    record_by_key = {(r.session_id, r.trainee_id): r for r in records}
    batch_lookup = {batch.id: batch for _session, batch in rows}
    acc: dict[tuple[int, int], dict] = {}

    for session, batch in rows:
        for enrollment in enrollment_by_batch.get(batch.id, []):
            key = (enrollment.trainee_id, batch.id)
            item = acc.setdefault(key, {
                "trainee_id": enrollment.trainee_id,
                "batch_id": batch.id,
                "total_sessions": 0,
                "present": 0,
                "late": 0,
                "absent": 0,
                "excused": 0,
            })
            record = record_by_key.get((session.id, enrollment.trainee_id))
            status_value = record.status if record and record.status in {"PRESENT", "LATE", "ABSENT", "EXCUSED"} else "ABSENT"
            item[status_value.lower()] += 1
            item["total_sessions"] += 1

    trainee_ids = {item["trainee_id"] for item in acc.values()}
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(trainee_ids))).all()} if trainee_ids else {}
    alerts: list[LowAttendanceAlert] = []
    for item in acc.values():
        rate = _rate(item["present"] + item["late"], item["total_sessions"])
        if rate < threshold:
            trainee = users.get(item["trainee_id"])
            batch = batch_lookup.get(item["batch_id"])
            if trainee and batch:
                alerts.append(LowAttendanceAlert(
                    trainee_id=trainee.id, trainee_name=trainee.full_name, trainee_email=trainee.email,
                    batch_id=batch.id, batch_code=batch.batch_code, total_sessions=item["total_sessions"],
                    present=item["present"], late=item["late"], absent=item["absent"], excused=item["excused"],
                    attendance_rate=rate, threshold=threshold,
                ))
    alerts.sort(key=lambda x: (x.attendance_rate, x.trainee_name.lower()))
    return LowAttendanceAlertResponse(threshold=threshold, alerts=alerts)


@router.get("/sessions", response_model=list[AttendanceSessionResponse])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(AttendanceSession).order_by(AttendanceSession.session_date.desc(), AttendanceSession.start_time.desc())
    if current_user.role == "TRAINEE":
        query = query.join(Enrollment, Enrollment.batch_id == AttendanceSession.batch_id).where(Enrollment.trainee_id == current_user.id)
    elif current_user.role not in {"NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER"}:
        return []
    return db.scalars(query).unique().all()


@router.post("/sessions", response_model=AttendanceSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(payload: AttendanceSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(MANAGERS)):
    batch = db.get(TrainingBatch, payload.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    existing = db.scalar(select(AttendanceSession).where(
        AttendanceSession.batch_id == payload.batch_id,
        AttendanceSession.session_date == payload.session_date,
        AttendanceSession.start_time == payload.start_time,
    ))
    if existing:
        raise HTTPException(status_code=409, detail="Attendance session already exists for this batch and time")
    session = AttendanceSession(**payload.model_dump(), access_code=_code(db), created_by_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{session_id}/roster", response_model=list[AttendanceRecordResponse])
def roster(session_id: int, db: Session = Depends(get_db), _user: User = Depends(MANAGERS)):
    session = _session(db, session_id)
    rows = db.execute(
        select(Enrollment, User).join(User, User.id == Enrollment.trainee_id).where(Enrollment.batch_id == session.batch_id, User.role == "TRAINEE")
    ).all()
    records = {r.trainee_id: r for r in db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)).all()}
    result: list[AttendanceRecordResponse] = []
    for enrollment, trainee in rows:
        record = records.get(trainee.id)
        if record is None:
            record = AttendanceRecord(session_id=session.id, trainee_id=trainee.id, status="ABSENT", method="SYSTEM")
            db.add(record)
            db.flush()
        result.append(_roster_row(record, trainee))
    db.commit()
    return result


@router.post("/sessions/{session_id}/mark", response_model=AttendanceRecordResponse)
def mark_attendance(session_id: int, payload: AttendanceRecordUpdate, db: Session = Depends(get_db), current_user: User = Depends(MANAGERS)):
    session = _session(db, session_id)
    trainee = db.get(User, payload.trainee_id)
    if not trainee or trainee.role != "TRAINEE" or not trainee.is_active:
        raise HTTPException(status_code=404, detail="Active trainee not found")
    enrolled = db.scalar(select(Enrollment).where(Enrollment.batch_id == session.batch_id, Enrollment.trainee_id == trainee.id, Enrollment.status == "ACTIVE"))
    if not enrolled:
        raise HTTPException(status_code=400, detail="Trainee is not actively enrolled in this batch")
    allowed = {"PRESENT", "ABSENT", "LATE", "EXCUSED"}
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid attendance status")
    record = db.scalar(select(AttendanceRecord).where(AttendanceRecord.session_id == session.id, AttendanceRecord.trainee_id == trainee.id))
    if not record:
        record = AttendanceRecord(session_id=session.id, trainee_id=trainee.id)
        db.add(record)
    record.status = payload.status
    record.method = "MANUAL"
    record.marked_by_id = current_user.id
    record.remarks = payload.remarks
    record.check_in_at = datetime.now(timezone.utc) if payload.status in {"PRESENT", "LATE"} else None
    db.commit()
    db.refresh(record)
    return _roster_row(record, trainee)


@router.post("/check-in", response_model=AttendanceRecordResponse)
def trainee_check_in(payload: AttendanceCheckIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "TRAINEE":
        raise HTTPException(status_code=403, detail="Only trainees can check in")
    session = db.scalar(select(AttendanceSession).where(AttendanceSession.access_code == payload.access_code.strip().upper()))
    if not session:
        raise HTTPException(status_code=404, detail="Attendance code not found")
    if session.status != "OPEN":
        raise HTTPException(status_code=400, detail="This attendance session is not open")
    enrolled = db.scalar(select(Enrollment).where(Enrollment.batch_id == session.batch_id, Enrollment.trainee_id == current_user.id, Enrollment.status == "ACTIVE"))
    if not enrolled:
        raise HTTPException(status_code=400, detail="You are not actively enrolled in this batch")
    record = db.scalar(select(AttendanceRecord).where(AttendanceRecord.session_id == session.id, AttendanceRecord.trainee_id == current_user.id))
    if not record:
        record = AttendanceRecord(session_id=session.id, trainee_id=current_user.id)
        db.add(record)
    record.status = "PRESENT"
    record.method = "QR"
    record.check_in_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return _roster_row(record, current_user)


@router.get("/sessions/{session_id}/qr", response_model=AttendanceQrResponse)
def attendance_qr(session_id: int, db: Session = Depends(get_db), _user: User = Depends(MANAGERS)):
    session = _session(db, session_id)
    payload = f"NCCT_ATTENDANCE:{session.access_code}"
    image = qrcode.make(payload)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    return AttendanceQrResponse(session_id=session.id, access_code=session.access_code, data_url=data_url)
