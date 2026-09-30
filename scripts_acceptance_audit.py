from pathlib import Path
import ast, re, sys

ROOT = Path(__file__).resolve().parent
errors=[]; checks=[]

def check(name, ok, detail=''):
    checks.append((name, ok, detail))
    if not ok: errors.append((name, detail))

# 1. Parse every Python source file.
py_files=list((ROOT/'backend').rglob('*.py'))
for p in py_files:
    try: ast.parse(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append((f'Python parse: {p}', str(e)))
check('Backend Python AST', not any(n.startswith('Python parse:') for n,_ in errors), f'{len(py_files)} files parsed')

# 2. Alembic must have one head, including the LMS branch merge.
versions={}
for p in (ROOT/'backend'/'alembic'/'versions').glob('*.py'):
    tree=ast.parse(p.read_text(encoding='utf-8'))
    vals={}
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id in {'revision','down_revision'}:
                    try: vals[t.id]=ast.literal_eval(n.value)
                    except Exception: pass
        elif isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id in {'revision','down_revision'} and n.value:
            try: vals[n.target.id]=ast.literal_eval(n.value)
            except Exception: pass
    if 'revision' in vals: versions[vals['revision']]=(p.name,vals.get('down_revision'))
children=set()
for _,(_,d) in versions.items():
    if isinstance(d,(tuple,list)): children.update(d)
    elif d: children.add(d)
heads=[r for r in versions if r not in children]
check('Alembic single head', heads==['0021_merge_all_heads'], f'heads={heads}')

# 3. Application router registration.
main=(ROOT/'backend/app/main.py').read_text(encoding='utf-8')
for name in ['training_schedule_router','training_logistics_router','training_evaluation_router','attendance_router','lms_router','credentials_router','careers_router','intelligence_router','dashboard_router','skills_router','skill_passport_router','skill_recommendation_router','notifications_router']:
    check(f'Router registered: {name}', name in main)

# 4. Schedule contract and guards.
schema=(ROOT/'backend/app/training/schedule_schemas.py').read_text(encoding='utf-8')
router=(ROOT/'backend/app/training/schedule_router.py').read_text(encoding='utf-8')
for field in ['batch_id','course_id','module_id','trainer_id','session_date','start_time','end_time','topic','venue','mode','status','notes']:
    check(f'Schedule field: {field}', re.search(rf'\b{field}\b', schema) is not None)
for guard in ['End time must be after start time','Session date must fall within the batch dates','Selected course does not belong to this batch programme','Selected module does not belong to the selected course','Selected trainer is not an active trainer']:
    check(f'Schedule guard: {guard[:28]}', guard in router)

# 5. Frontend training API/UI contract.
api=(ROOT/'frontend/src/modules/training/api.ts').read_text(encoding='utf-8')
erp=(ROOT/'frontend/src/modules/training/TrainingERP.tsx').read_text(encoding='utf-8')
for s in ['getTrainingSchedules','createTrainingSchedule','createAttendanceForSchedule','/training/schedules']:
    check(f'Frontend schedule support: {s}', s in api)
for s in ['scheduleCourses','scheduleModules','selectedScheduleBatch','Session date must be between','End time must be after start time','min={selectedScheduleBatch?.start_date}','max={selectedScheduleBatch?.end_date}']:
    check(f'Frontend schedule hardening: {s[:32]}', s in erp)

# 6. Core module source presence.
modules=[
 'Dashboard','Notifications','TrainingERP','TrainingLogistics','TrainingEvaluation','Attendance','LMS',
 'SkillsCredentials','VerifyCredential','SkillRecommendations','Careers','Intelligence','Administration','DigitalLiteracy'
]
for m in modules:
    matches=list((ROOT/'frontend/src/modules').glob(f'*/{m}.tsx'))
    check(f'Frontend module: {m}', bool(matches))

print('NCCT ACCEPTANCE AUDIT')
print('='*80)
for name,ok,detail in checks:
    print(('PASS' if ok else 'FAIL').ljust(5), name, ('— '+detail) if detail else '')
print('='*80)
print(f'PASS={sum(1 for _,o,_ in checks if o)} FAIL={sum(1 for _,o,_ in checks if not o)}')
if errors:
    print('FAILURES:')
    for n,d in errors: print('-',n,d)
    sys.exit(1)
