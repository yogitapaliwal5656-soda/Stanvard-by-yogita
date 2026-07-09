"""Stanvard School ERP - FastAPI backend."""
import os
import logging
import hmac
import hashlib
import io
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import razorpay

from database import (
    db, mongo_client,
    schools_col, users_col, students_col, classes_col,
    fee_heads_col, fee_plans_col, fee_assignments_col,
    payments_col, receipts_col, razorpay_orders_col,
    attendance_col, homework_col, timetable_col,
    events_col, circulars_col, gallery_col, staff_col,
    notifications_col, audit_col, settings_col,
    get_next_sequence,
)
from models import (
    School, SchoolCreate, SchoolUpdate,
    User, UserCreate, UserUpdate, LoginRequest, LoginResponse,
    Student, StudentCreate, StudentUpdate,
    ClassRoom, ClassCreate,
    FeeHead, FeeHeadCreate, FeePlan, FeePlanCreate, FeeAssignment, FeeAssignmentCreate,
    FeeAssignmentUpdate, FeeAssignmentItem,
    Payment, PaymentCreate, PaymentLineItem,
    RazorpayOrderRequest, RazorpayVerifyRequest,
    AttendanceRecord, AttendanceBulkMark,
    Homework, HomeworkCreate,
    Timetable, TimetableCreate,
    Event, EventCreate,
    Circular, CircularCreate,
    GalleryAlbum, GalleryAlbumCreate,
    Staff, StaffCreate,
    Notification, NotificationCreate,
    SchoolSettings,
    now_iso, new_id,
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_roles, current_school_id, resolve_school_id, resolve_school_id_safe,
)
from audit import log_audit
from pdf_utils import generate_receipt_pdf, generate_report_pdf

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')

rzp_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

app = FastAPI(title='Stanvard School ERP API', version='1.0.0')
api = APIRouter(prefix='/api')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('stanvard')

# ----- utils -----
def strip_password(u: dict) -> dict:
    d = dict(u or {})
    d.pop('password_hash', None)
    d.pop('_id', None)
    return d


def clean(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [clean(d) for d in doc]
    if isinstance(doc, dict):
        return {k: v for k, v in doc.items() if k != '_id'}
    return doc


# =====================================================
# HEALTH / ROOT
# =====================================================
@api.get('/')
async def root():
    return {'app': 'Stanvard School ERP', 'status': 'running'}


@api.get('/health')
async def health():
    return {'ok': True, 'time': now_iso()}


# =====================================================
# AUTH
# =====================================================
@api.post('/auth/login', response_model=LoginResponse)
async def login(body: LoginRequest, request: Request):
    user = await users_col.find_one({'email': body.email.lower()}, {'_id': 0})
    if not user or not verify_password(body.password, user.get('password_hash', '')):
        raise HTTPException(status_code=401, detail='Invalid email or password')
    if user.get('status') != 'active':
        raise HTTPException(status_code=403, detail='Account is inactive')
    token = create_access_token({'sub': user['id'], 'role': user['role']})
    await log_audit(action='auth.login', current_user=user,
                    ip_address=request.client.host if request.client else None)
    return LoginResponse(access_token=token, user=strip_password(user))


@api.get('/auth/me')
async def me(current=Depends(get_current_user)):
    return strip_password(current)


@api.get('/auth/my-schools')
async def my_schools(current=Depends(get_current_user)):
    """Schools accessible to current user."""
    if current['role'] == 'super_admin':
        rows = await schools_col.find({'status': {'$ne': 'deleted'}}, {'_id': 0}).to_list(1000)
    else:
        sid = current.get('school_id')
        rows = await schools_col.find({'id': sid}, {'_id': 0}).to_list(1) if sid else []
    return rows


# =====================================================
# SCHOOLS (super admin)
# =====================================================
@api.get('/schools')
async def list_schools(current=Depends(get_current_user)):
    if current['role'] == 'super_admin':
        rows = await schools_col.find({'status': {'$ne': 'deleted'}}, {'_id': 0}).to_list(1000)
    else:
        sid = current.get('school_id')
        rows = await schools_col.find({'id': sid}, {'_id': 0}).to_list(1) if sid else []
    return rows


@api.post('/schools', dependencies=[Depends(require_roles('super_admin'))])
async def create_school(body: SchoolCreate, current=Depends(get_current_user)):
    s = School(**body.model_dump())
    doc = s.model_dump()
    await schools_col.insert_one(doc)
    await log_audit(action='school.create', current_user=current,
                    entity_type='school', entity_id=s.id, details={'name': s.name})
    return clean(doc)


@api.patch('/schools/{school_id}', dependencies=[Depends(require_roles('super_admin'))])
async def update_school(school_id: str, body: SchoolUpdate, current=Depends(get_current_user)):
    upd = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    upd['updated_at'] = now_iso()
    r = await schools_col.update_one({'id': school_id}, {'$set': upd})
    if not r.matched_count:
        raise HTTPException(404, 'School not found')
    await log_audit(action='school.update', current_user=current,
                    entity_type='school', entity_id=school_id, details=upd)
    doc = await schools_col.find_one({'id': school_id}, {'_id': 0})
    return clean(doc)


@api.delete('/schools/{school_id}', dependencies=[Depends(require_roles('super_admin'))])
async def archive_school(school_id: str, current=Depends(get_current_user)):
    r = await schools_col.update_one({'id': school_id},
                                     {'$set': {'status': 'archived', 'updated_at': now_iso()}})
    if not r.matched_count:
        raise HTTPException(404, 'School not found')
    await log_audit(action='school.archive', current_user=current,
                    entity_type='school', entity_id=school_id)
    return {'ok': True}


# =====================================================
# USERS
# =====================================================
@api.get('/users')
async def list_users(current=Depends(get_current_user),
                    role: Optional[str] = None,
                    school_id: Optional[str] = None):
    q: Dict[str, Any] = {}
    if role:
        q['role'] = role
    if current['role'] == 'super_admin':
        if school_id:
            q['school_id'] = school_id
    else:
        q['school_id'] = current['school_id']
    rows = await users_col.find(q, {'_id': 0}).to_list(2000)
    return [strip_password(r) for r in rows]


@api.post('/users', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def create_user(body: UserCreate, current=Depends(get_current_user)):
    if body.role not in {'super_admin', 'school_admin', 'accountant', 'teacher', 'parent'}:
        raise HTTPException(400, 'Invalid role')
    if current['role'] == 'school_admin':
        # school admin cannot create super_admin, and must scope to own school
        if body.role == 'super_admin':
            raise HTTPException(403, 'Cannot create super admin')
        body.school_id = current['school_id']
    exists = await users_col.find_one({'email': body.email.lower()}, {'_id': 0})
    if exists:
        raise HTTPException(400, 'Email already registered')
    u = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        school_id=body.school_id,
        phone=body.phone,
        linked_student_id=body.linked_student_id,
        linked_class_ids=body.linked_class_ids,
    )
    await users_col.insert_one(u.model_dump())
    await log_audit(action='user.create', current_user=current,
                    entity_type='user', entity_id=u.id,
                    details={'email': u.email, 'role': u.role})
    return strip_password(u.model_dump())


@api.patch('/users/{user_id}', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def update_user(user_id: str, body: UserUpdate, current=Depends(get_current_user)):
    upd: Dict[str, Any] = {}
    for k, v in body.model_dump(exclude_none=True).items():
        if k == 'password':
            upd['password_hash'] = hash_password(v)
        else:
            upd[k] = v
    upd['updated_at'] = now_iso()
    r = await users_col.update_one({'id': user_id}, {'$set': upd})
    if not r.matched_count:
        raise HTTPException(404, 'User not found')
    await log_audit(action='user.update', current_user=current,
                    entity_type='user', entity_id=user_id, details={k: v for k, v in upd.items() if k != 'password_hash'})
    doc = await users_col.find_one({'id': user_id}, {'_id': 0})
    return strip_password(doc)


# =====================================================
# STUDENTS
# =====================================================
@api.get('/students')
async def list_students(request: Request,
                        current=Depends(get_current_user),
                        school_id: Optional[str] = None,
                        class_id: Optional[str] = None,
                        section: Optional[str] = None,
                        status: Optional[str] = None,
                        search: Optional[str] = None,
                        limit: int = 500):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    q: Dict[str, Any] = {'school_id': sid}
    # For parent role, restrict to their linked student
    if current['role'] == 'parent' and current.get('linked_student_id'):
        q['id'] = current['linked_student_id']
    if class_id:
        q['class_id'] = class_id
    if section:
        q['section'] = section
    if status:
        q['status'] = status
    if search:
        q['$or'] = [
            {'full_name': {'$regex': search, '$options': 'i'}},
            {'admission_number': {'$regex': search, '$options': 'i'}},
            {'father_name': {'$regex': search, '$options': 'i'}},
            {'phone': {'$regex': search, '$options': 'i'}},
        ]
    rows = await students_col.find(q, {'_id': 0}).limit(limit).to_list(limit)
    return rows


@api.get('/students/{student_id}')
async def get_student(student_id: str, request: Request, current=Depends(get_current_user)):
    s = await students_col.find_one({'id': student_id}, {'_id': 0})
    if not s:
        raise HTTPException(404, 'Student not found')
    # scope check
    if current['role'] != 'super_admin' and s['school_id'] != current.get('school_id'):
        raise HTTPException(403, 'Forbidden')
    if current['role'] == 'parent' and current.get('linked_student_id') != student_id:
        raise HTTPException(403, 'Forbidden')
    return s


@api.post('/students', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def create_student(body: StudentCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    adm_no = body.admission_number
    if not adm_no:
        seq = await get_next_sequence(f'adm_{sid}')
        school = await schools_col.find_one({'id': sid}, {'_id': 0})
        code = (school or {}).get('code', 'STV')
        adm_no = f'{code}-2025-{seq:04d}'
    data = body.model_dump(exclude_none=True)
    data.pop('school_id', None)
    student = Student(school_id=sid, admission_number=adm_no, **{k: v for k, v in data.items() if k != 'admission_number'})
    await students_col.insert_one(student.model_dump())
    await log_audit(action='student.create', current_user=current, school_id=sid,
                    entity_type='student', entity_id=student.id,
                    details={'admission_number': adm_no, 'name': student.full_name})
    return student.model_dump()


@api.patch('/students/{student_id}', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def update_student(student_id: str, body: StudentUpdate, current=Depends(get_current_user)):
    upd = body.model_dump(exclude_none=True)
    upd['updated_at'] = now_iso()
    r = await students_col.update_one({'id': student_id}, {'$set': upd})
    if not r.matched_count:
        raise HTTPException(404, 'Student not found')
    await log_audit(action='student.update', current_user=current,
                    entity_type='student', entity_id=student_id, details=upd)
    return await students_col.find_one({'id': student_id}, {'_id': 0})


@api.delete('/students/{student_id}', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def delete_student(student_id: str, current=Depends(get_current_user)):
    r = await students_col.update_one({'id': student_id},
                                      {'$set': {'status': 'inactive', 'updated_at': now_iso()}})
    if not r.matched_count:
        raise HTTPException(404, 'Student not found')
    await log_audit(action='student.delete', current_user=current,
                    entity_type='student', entity_id=student_id)
    return {'ok': True}


# =====================================================
# CLASSES
# =====================================================
@api.get('/classes')
async def list_classes(request: Request, current=Depends(get_current_user),
                       school_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    rows = await classes_col.find({'school_id': sid}, {'_id': 0}).to_list(1000)
    return rows


@api.post('/classes', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def create_class(body: ClassCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    c = ClassRoom(school_id=sid, name=body.name, sections=body.sections, teacher_id=body.teacher_id)
    await classes_col.insert_one(c.model_dump())
    await log_audit(action='class.create', current_user=current, school_id=sid,
                    entity_type='class', entity_id=c.id, details={'name': c.name})
    return c.model_dump()


# =====================================================
# FEE HEADS
# =====================================================
@api.get('/fees/heads')
async def list_fee_heads(request: Request, current=Depends(get_current_user),
                        school_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    return await fee_heads_col.find({'school_id': sid}, {'_id': 0}).to_list(500)


@api.post('/fees/heads', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def create_fee_head(body: FeeHeadCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    fh = FeeHead(school_id=sid, name=body.name, category=body.category)
    await fee_heads_col.insert_one(fh.model_dump())
    await log_audit(action='fee_head.create', current_user=current, school_id=sid,
                    entity_type='fee_head', entity_id=fh.id, details={'name': fh.name})
    return fh.model_dump()


# =====================================================
# FEE PLANS
# =====================================================
@api.get('/fees/plans')
async def list_fee_plans(request: Request, current=Depends(get_current_user),
                        school_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    return await fee_plans_col.find({'school_id': sid}, {'_id': 0}).to_list(500)


@api.post('/fees/plans', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def create_fee_plan(body: FeePlanCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    p = FeePlan(school_id=sid, name=body.name, academic_session=body.academic_session,
                class_id=body.class_id, items=body.items,
                annual_discount_percent=body.annual_discount_percent,
                late_fee_amount=body.late_fee_amount, late_fee_after_day=body.late_fee_after_day)
    await fee_plans_col.insert_one(p.model_dump())
    await log_audit(action='fee_plan.create', current_user=current, school_id=sid,
                    entity_type='fee_plan', entity_id=p.id, details={'name': p.name})
    return p.model_dump()


@api.patch('/fees/plans/{plan_id}', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def update_fee_plan(plan_id: str, body: FeePlanCreate, current=Depends(get_current_user)):
    upd = body.model_dump(exclude_none=True)
    upd.pop('school_id', None)
    upd['updated_at'] = now_iso()
    r = await fee_plans_col.update_one({'id': plan_id}, {'$set': upd})
    if not r.matched_count:
        raise HTTPException(404, 'Plan not found')
    await log_audit(action='fee_plan.update', current_user=current,
                    entity_type='fee_plan', entity_id=plan_id, details=upd)
    return await fee_plans_col.find_one({'id': plan_id}, {'_id': 0})


@api.post('/fees/plans/{plan_id}/assign', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def assign_plan(plan_id: str, student_ids: List[str], request: Request,
                     current=Depends(get_current_user)):
    plan = await fee_plans_col.find_one({'id': plan_id}, {'_id': 0})
    if not plan:
        raise HTTPException(404, 'Plan not found')
    assignments = []
    for sid_ in student_ids:
        exists = await fee_assignments_col.find_one({'student_id': sid_, 'fee_plan_id': plan_id, 'academic_session': plan['academic_session']}, {'_id': 0})
        if exists:
            continue
        a = FeeAssignment(school_id=plan['school_id'], student_id=sid_, fee_plan_id=plan_id,
                          academic_session=plan['academic_session'])
        await fee_assignments_col.insert_one(a.model_dump())
        assignments.append(a.model_dump())
    await log_audit(action='fee_plan.assign', current_user=current, school_id=plan['school_id'],
                    entity_type='fee_plan', entity_id=plan_id,
                    details={'count': len(assignments)})
    return {'assigned': len(assignments)}


@api.get('/fees/student/{student_id}/dues')
async def student_dues(student_id: str, request: Request, current=Depends(get_current_user)):
    student = await students_col.find_one({'id': student_id}, {'_id': 0})
    if not student:
        raise HTTPException(404, 'Student not found')
    if current['role'] == 'parent' and current.get('linked_student_id') != student_id:
        raise HTTPException(403, 'Forbidden')
    assignments = await fee_assignments_col.find({'student_id': student_id}, {'_id': 0}).to_list(50)
    dues = []
    total_expected = 0.0
    total_discount = 0.0
    for a in assignments:
        # Custom items take priority over plan
        items_for_a = []
        if a.get('custom_items'):
            items_for_a = a['custom_items']
        elif a.get('fee_plan_id'):
            plan = await fee_plans_col.find_one({'id': a['fee_plan_id']}, {'_id': 0})
            if plan:
                items_for_a = plan.get('items', [])
        for item in items_for_a:
            entry = {
                'fee_head_id': item.get('fee_head_id'),
                'fee_head_name': item.get('fee_head_name'),
                'amount': item.get('amount', 0),
                'frequency': item.get('frequency', 'monthly'),
                'installments': item.get('installments', 1) if 'installments' in item else 1,
                'due_date': item.get('due_date') or a.get('due_date'),
                'assignment_id': a['id'],
                'plan_id': a.get('fee_plan_id'),
            }
            dues.append(entry)
            total_expected += entry['amount']
        # Apply assignment-level discount
        if a.get('discount_percent'):
            total_discount += total_expected * (a['discount_percent'] / 100)
        if a.get('discount_amount'):
            total_discount += a['discount_amount']
    # payments
    payments = await payments_col.find({'student_id': student_id, 'status': 'success'}, {'_id': 0}).to_list(500)
    total_paid = sum(p.get('total_paid', 0) for p in payments)
    balance = max(total_expected - total_discount - total_paid, 0)
    return {
        'student': student,
        'dues': dues,
        'assignments': assignments,
        'total_expected': total_expected,
        'total_discount': total_discount,
        'total_paid': total_paid,
        'balance': balance,
        'recent_payments': sorted(payments, key=lambda x: x.get('paid_at', ''), reverse=True)[:10],
    }


# ---------- FEE ASSIGNMENTS (per-student) ----------
@api.get('/fees/assignments')
async def list_assignments(request: Request, current=Depends(get_current_user),
                           school_id: Optional[str] = None,
                           student_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    q: Dict[str, Any] = {'school_id': sid}
    if student_id:
        q['student_id'] = student_id
    return await fee_assignments_col.find(q, {'_id': 0}).to_list(500)


@api.post('/fees/assignments', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def create_assignment(body: FeeAssignmentCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    a = FeeAssignment(
        school_id=sid, student_id=body.student_id, fee_plan_id=body.fee_plan_id,
        academic_session=body.academic_session,
        custom_items=body.custom_items or [],
        custom_amount=body.custom_amount,
        discount_percent=body.discount_percent or 0.0,
        discount_amount=body.discount_amount or 0.0,
        due_date=body.due_date, remarks=body.remarks,
    )
    await fee_assignments_col.insert_one(a.model_dump())
    await log_audit(action='fee_assignment.create', current_user=current, school_id=sid,
                    entity_type='fee_assignment', entity_id=a.id,
                    details={'student_id': body.student_id, 'discount_percent': body.discount_percent,
                             'discount_amount': body.discount_amount, 'due_date': body.due_date})
    return a.model_dump()


@api.patch('/fees/assignments/{assignment_id}', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def update_assignment(assignment_id: str, body: FeeAssignmentUpdate, current=Depends(get_current_user)):
    upd = body.model_dump(exclude_none=True)
    upd['updated_at'] = now_iso()
    r = await fee_assignments_col.update_one({'id': assignment_id}, {'$set': upd})
    if not r.matched_count:
        raise HTTPException(404, 'Assignment not found')
    await log_audit(action='fee_assignment.update', current_user=current,
                    entity_type='fee_assignment', entity_id=assignment_id, details=upd)
    return await fee_assignments_col.find_one({'id': assignment_id}, {'_id': 0})


@api.delete('/fees/assignments/{assignment_id}', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def delete_assignment(assignment_id: str, current=Depends(get_current_user)):
    r = await fee_assignments_col.delete_one({'id': assignment_id})
    if not r.deleted_count:
        raise HTTPException(404, 'Assignment not found')
    await log_audit(action='fee_assignment.delete', current_user=current,
                    entity_type='fee_assignment', entity_id=assignment_id)
    return {'ok': True}


# =====================================================
# PAYMENTS / RECEIPTS
# =====================================================
async def _generate_receipt_number(school_id: str) -> str:
    school = await schools_col.find_one({'id': school_id}, {'_id': 0})
    code = (school or {}).get('code', 'STV')
    seq = await get_next_sequence(f'receipt_{school_id}')
    year = datetime.now().year
    return f'{code}-{year}-{seq:06d}'


async def _finalize_payment(school_id: str, body: PaymentCreate, current: dict,
                            razorpay_order_id: Optional[str] = None,
                            razorpay_payment_id: Optional[str] = None,
                            razorpay_signature: Optional[str] = None) -> Payment:
    student = await students_col.find_one({'id': body.student_id}, {'_id': 0})
    if not student:
        raise HTTPException(404, 'Student not found')
    subtotal = sum(i.amount for i in body.items)
    total_paid = subtotal + body.late_fee - body.discount
    receipt_no = await _generate_receipt_number(school_id)
    payment = Payment(
        school_id=school_id,
        student_id=student['id'],
        student_name=student['full_name'],
        receipt_number=receipt_no,
        items=body.items,
        subtotal=subtotal,
        discount=body.discount,
        late_fee=body.late_fee,
        total_paid=total_paid,
        payment_mode=body.payment_mode,
        txn_ref=body.txn_ref,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
        status='success',
        remarks=body.remarks,
        collected_by_id=current.get('id'),
        collected_by_name=current.get('full_name'),
    )
    await payments_col.insert_one(payment.model_dump())
    await log_audit(action='payment.collect', current_user=current, school_id=school_id,
                    entity_type='payment', entity_id=payment.id,
                    details={'receipt_number': receipt_no, 'total': total_paid,
                             'mode': body.payment_mode, 'student': student['full_name']})
    return payment


@api.post('/payments/collect', dependencies=[Depends(require_roles('super_admin', 'school_admin', 'accountant'))])
async def collect_payment(body: PaymentCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    payment = await _finalize_payment(sid, body, current)
    return payment.model_dump()


@api.post('/payments/razorpay/order')
async def razorpay_create_order(body: RazorpayOrderRequest, request: Request,
                                current=Depends(get_current_user)):
    if not rzp_client:
        raise HTTPException(500, 'Razorpay not configured')
    student = await students_col.find_one({'id': body.student_id}, {'_id': 0})
    if not student:
        raise HTTPException(404, 'Student not found')
    if current['role'] == 'parent' and current.get('linked_student_id') != body.student_id:
        raise HTTPException(403, 'Forbidden')
    subtotal = sum(i.amount for i in body.items)
    total = subtotal + body.late_fee - body.discount
    amount_paise = int(round(total * 100))
    if amount_paise <= 0:
        raise HTTPException(400, 'Amount must be > 0')
    receipt_ref = f'stv_{new_id()[:8]}'
    order = rzp_client.order.create(data={
        'amount': amount_paise, 'currency': 'INR',
        'receipt': receipt_ref, 'payment_capture': 1,
        'notes': {
            'school_id': student['school_id'],
            'student_id': student['id'],
            'student_name': student['full_name'],
        }
    })
    await razorpay_orders_col.insert_one({
        'id': order['id'],
        'school_id': student['school_id'],
        'student_id': student['id'],
        'amount': total,
        'items': [i.model_dump() for i in body.items],
        'discount': body.discount,
        'late_fee': body.late_fee,
        'remarks': body.remarks,
        'status': 'created',
        'created_at': now_iso(),
    })
    return {
        'order_id': order['id'],
        'amount': amount_paise,
        'currency': 'INR',
        'key_id': RAZORPAY_KEY_ID,
        'student_name': student['full_name'],
    }


@api.post('/payments/razorpay/verify')
async def razorpay_verify(body: RazorpayVerifyRequest, request: Request,
                          current=Depends(get_current_user)):
    if not rzp_client:
        raise HTTPException(500, 'Razorpay not configured')
    # Verify signature
    payload = f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode()
    expected = hmac.new(RAZORPAY_KEY_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, body.razorpay_signature):
        raise HTTPException(400, 'Signature verification failed')
    order = await razorpay_orders_col.find_one({'id': body.razorpay_order_id}, {'_id': 0})
    if not order:
        raise HTTPException(404, 'Order not found')
    if order['status'] == 'paid':
        # idempotent
        pay = await payments_col.find_one({'razorpay_order_id': body.razorpay_order_id}, {'_id': 0})
        return pay
    pc = PaymentCreate(
        school_id=order['school_id'],
        student_id=order['student_id'],
        items=[PaymentLineItem(**i) for i in order['items']],
        discount=order.get('discount', 0),
        late_fee=order.get('late_fee', 0),
        payment_mode='razorpay',
        txn_ref=body.razorpay_payment_id,
        remarks=order.get('remarks'),
    )
    payment = await _finalize_payment(order['school_id'], pc, current,
                                      razorpay_order_id=body.razorpay_order_id,
                                      razorpay_payment_id=body.razorpay_payment_id,
                                      razorpay_signature=body.razorpay_signature)
    await razorpay_orders_col.update_one({'id': body.razorpay_order_id},
                                         {'$set': {'status': 'paid', 'payment_id': payment.id}})
    return payment.model_dump()


@api.post('/payments/razorpay/webhook')
async def razorpay_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get('X-Razorpay-Signature', '')
    secret = RAZORPAY_WEBHOOK_SECRET or RAZORPAY_KEY_SECRET
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(400, 'Bad webhook signature')
    # Optionally handle events here
    return {'ok': True}


@api.get('/payments')
async def list_payments(request: Request, current=Depends(get_current_user),
                        school_id: Optional[str] = None,
                        student_id: Optional[str] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        mode: Optional[str] = None,
                        limit: int = 500):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    q: Dict[str, Any] = {'school_id': sid}
    if current['role'] == 'parent' and current.get('linked_student_id'):
        q['student_id'] = current['linked_student_id']
    if student_id:
        q['student_id'] = student_id
    if mode:
        q['payment_mode'] = mode
    if start_date or end_date:
        rq: Dict[str, Any] = {}
        if start_date:
            rq['$gte'] = start_date
        if end_date:
            rq['$lte'] = end_date + 'T23:59:59'
        q['paid_at'] = rq
    rows = await payments_col.find(q, {'_id': 0}).sort('paid_at', -1).limit(limit).to_list(limit)
    return rows


@api.get('/payments/{payment_id}')
async def get_payment(payment_id: str, current=Depends(get_current_user)):
    p = await payments_col.find_one({'id': payment_id}, {'_id': 0})
    if not p:
        raise HTTPException(404, 'Payment not found')
    if current['role'] != 'super_admin' and p['school_id'] != current.get('school_id'):
        raise HTTPException(403, 'Forbidden')
    if current['role'] == 'parent' and p['student_id'] != current.get('linked_student_id'):
        raise HTTPException(403, 'Forbidden')
    return p


@api.get('/payments/{payment_id}/receipt.pdf')
async def download_receipt(payment_id: str, current=Depends(get_current_user)):
    p = await payments_col.find_one({'id': payment_id}, {'_id': 0})
    if not p:
        raise HTTPException(404, 'Payment not found')
    if current['role'] != 'super_admin' and p['school_id'] != current.get('school_id'):
        raise HTTPException(403, 'Forbidden')
    if current['role'] == 'parent' and p['student_id'] != current.get('linked_student_id'):
        raise HTTPException(403, 'Forbidden')
    school = await schools_col.find_one({'id': p['school_id']}, {'_id': 0}) or {}
    student = await students_col.find_one({'id': p['student_id']}, {'_id': 0}) or {}
    # enrich with class name
    if student.get('class_id'):
        cls = await classes_col.find_one({'id': student['class_id']}, {'_id': 0})
        if cls:
            student['class_name'] = cls['name']
    pdf_bytes = generate_receipt_pdf(p, school, student)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type='application/pdf',
        headers={'Content-Disposition': f'inline; filename="receipt_{p["receipt_number"]}.pdf"'}
    )


# =====================================================
# ATTENDANCE
# =====================================================
@api.post('/attendance/mark', dependencies=[Depends(require_roles('super_admin', 'school_admin', 'teacher'))])
async def mark_attendance(body: AttendanceBulkMark, request: Request,
                          current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    # Delete existing for that date/class first (upsert semantics)
    await attendance_col.delete_many({
        'school_id': sid,
        'date': body.date,
        'class_id': body.class_id,
        'section': body.section,
    })
    docs = []
    for e in body.entries:
        rec = AttendanceRecord(
            school_id=sid, date=body.date, class_id=body.class_id,
            section=body.section, student_id=e.get('student_id'),
            status=e.get('status', 'present'),
            remarks=e.get('remarks'),
            marked_by_id=current.get('id'),
        )
        docs.append(rec.model_dump())
    if docs:
        await attendance_col.insert_many(docs)
    await log_audit(action='attendance.mark', current_user=current, school_id=sid,
                    entity_type='attendance', entity_id=f"{body.date}-{body.class_id}",
                    details={'count': len(docs), 'date': body.date})
    return {'saved': len(docs)}


@api.get('/attendance')
async def list_attendance(request: Request, current=Depends(get_current_user),
                          school_id: Optional[str] = None,
                          date: Optional[str] = None,
                          class_id: Optional[str] = None,
                          section: Optional[str] = None,
                          student_id: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    q: Dict[str, Any] = {'school_id': sid}
    if date:
        q['date'] = date
    if class_id:
        q['class_id'] = class_id
    if section:
        q['section'] = section
    if student_id:
        q['student_id'] = student_id
    if current['role'] == 'parent' and current.get('linked_student_id'):
        q['student_id'] = current['linked_student_id']
    if start_date or end_date:
        rq: Dict[str, Any] = {}
        if start_date:
            rq['$gte'] = start_date
        if end_date:
            rq['$lte'] = end_date
        q['date'] = rq if rq else q.get('date')
    rows = await attendance_col.find(q, {'_id': 0}).limit(5000).to_list(5000)
    return rows


# =====================================================
# HOMEWORK
# =====================================================
@api.get('/homework')
async def list_homework(request: Request, current=Depends(get_current_user),
                        school_id: Optional[str] = None,
                        class_id: Optional[str] = None,
                        section: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    q: Dict[str, Any] = {'school_id': sid}
    if class_id:
        q['class_id'] = class_id
    if section:
        q['section'] = section
    if current['role'] == 'parent' and current.get('linked_student_id'):
        student = await students_col.find_one({'id': current['linked_student_id']}, {'_id': 0})
        if student and student.get('class_id'):
            q['class_id'] = student['class_id']
            if student.get('section'):
                q['section'] = student['section']
    rows = await homework_col.find(q, {'_id': 0}).sort('created_at', -1).limit(500).to_list(500)
    return rows


@api.post('/homework', dependencies=[Depends(require_roles('super_admin', 'school_admin', 'teacher'))])
async def create_homework(body: HomeworkCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    hw = Homework(school_id=sid, class_id=body.class_id, section=body.section,
                  subject=body.subject, title=body.title, description=body.description,
                  due_date=body.due_date, attachment_url=body.attachment_url,
                  created_by_id=current.get('id'),
                  created_by_name=current.get('full_name'))
    await homework_col.insert_one(hw.model_dump())
    await log_audit(action='homework.create', current_user=current, school_id=sid,
                    entity_type='homework', entity_id=hw.id, details={'title': hw.title})
    return hw.model_dump()


# =====================================================
# TIMETABLE
# =====================================================
@api.get('/timetable')
async def get_timetable(request: Request, current=Depends(get_current_user),
                        school_id: Optional[str] = None,
                        class_id: Optional[str] = None,
                        section: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    q: Dict[str, Any] = {'school_id': sid}
    if class_id:
        q['class_id'] = class_id
    if section:
        q['section'] = section
    return await timetable_col.find(q, {'_id': 0}).to_list(200)


@api.post('/timetable', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def upsert_timetable(body: TimetableCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    exists = await timetable_col.find_one({'school_id': sid, 'class_id': body.class_id, 'section': body.section}, {'_id': 0})
    slots = [s.model_dump() for s in body.slots]
    if exists:
        await timetable_col.update_one({'id': exists['id']}, {'$set': {'slots': slots, 'updated_at': now_iso()}})
        return await timetable_col.find_one({'id': exists['id']}, {'_id': 0})
    t = Timetable(school_id=sid, class_id=body.class_id, section=body.section, slots=body.slots)
    await timetable_col.insert_one(t.model_dump())
    return t.model_dump()


# =====================================================
# EVENTS, CIRCULARS, GALLERY, STAFF, NOTIFICATIONS
# =====================================================
@api.get('/events')
async def list_events(request: Request, current=Depends(get_current_user), school_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    return await events_col.find({'school_id': sid}, {'_id': 0}).sort('event_date', -1).limit(200).to_list(200)


@api.post('/events', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def create_event(body: EventCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    e = Event(school_id=sid, title=body.title, description=body.description,
              event_date=body.event_date, location=body.location, image_url=body.image_url)
    await events_col.insert_one(e.model_dump())
    await log_audit(action='event.create', current_user=current, school_id=sid,
                    entity_type='event', entity_id=e.id, details={'title': e.title})
    return e.model_dump()


@api.get('/circulars')
async def list_circulars(request: Request, current=Depends(get_current_user), school_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    return await circulars_col.find({'school_id': sid, 'status': 'published'}, {'_id': 0}).sort('created_at', -1).limit(200).to_list(200)


@api.post('/circulars', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def create_circular(body: CircularCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    c = Circular(school_id=sid, title=body.title, body=body.body, priority=body.priority,
                 status=body.status, publish_at=body.publish_at,
                 attachment_url=body.attachment_url, audience=body.audience,
                 class_id=body.class_id, created_by_name=current.get('full_name'))
    await circulars_col.insert_one(c.model_dump())
    await log_audit(action='circular.create', current_user=current, school_id=sid,
                    entity_type='circular', entity_id=c.id, details={'title': c.title})
    return c.model_dump()


@api.get('/gallery')
async def list_gallery(request: Request, current=Depends(get_current_user), school_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    return await gallery_col.find({'school_id': sid}, {'_id': 0}).sort('created_at', -1).to_list(200)


@api.post('/gallery', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def create_album(body: GalleryAlbumCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    a = GalleryAlbum(school_id=sid, title=body.title, description=body.description,
                     cover_url=body.cover_url, photos=body.photos)
    await gallery_col.insert_one(a.model_dump())
    await log_audit(action='gallery.create', current_user=current, school_id=sid,
                    entity_type='gallery', entity_id=a.id, details={'title': a.title})
    return a.model_dump()


@api.get('/staff')
async def list_staff(request: Request, current=Depends(get_current_user), school_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    return await staff_col.find({'school_id': sid}, {'_id': 0}).to_list(500)


@api.post('/staff', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def create_staff(body: StaffCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    s = Staff(school_id=sid, full_name=body.full_name, email=body.email, phone=body.phone,
              designation=body.designation, department=body.department,
              subjects=body.subjects, joining_date=body.joining_date, photo_url=body.photo_url)
    await staff_col.insert_one(s.model_dump())
    await log_audit(action='staff.create', current_user=current, school_id=sid,
                    entity_type='staff', entity_id=s.id, details={'name': s.full_name})
    return s.model_dump()


@api.get('/notifications')
async def list_notifications(request: Request, current=Depends(get_current_user), school_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    q: Dict[str, Any] = {'school_id': sid}
    # audience filter for role-scoped users
    if current['role'] == 'parent':
        q['$or'] = [{'audience': 'all'}, {'audience': 'parents'},
                    {'student_ids': current.get('linked_student_id')}]
    elif current['role'] == 'teacher':
        q['$or'] = [{'audience': 'all'}, {'audience': 'teachers'}]
    return await notifications_col.find(q, {'_id': 0}).sort('created_at', -1).limit(200).to_list(200)


@api.post('/notifications', dependencies=[Depends(require_roles('super_admin', 'school_admin', 'teacher'))])
async def create_notification(body: NotificationCreate, request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, body.school_id, request.headers.get('X-School-Id'))
    n = Notification(school_id=sid, title=body.title, body=body.body,
                     audience=body.audience, class_id=body.class_id,
                     student_ids=body.student_ids, kind=body.kind)
    await notifications_col.insert_one(n.model_dump())
    await log_audit(action='notification.create', current_user=current, school_id=sid,
                    entity_type='notification', entity_id=n.id,
                    details={'title': n.title, 'audience': n.audience})
    return n.model_dump()


# =====================================================
# REPORTS
# =====================================================
@api.get('/reports/collection')
async def report_collection(request: Request, current=Depends(get_current_user),
                            school_id: Optional[str] = None,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    q: Dict[str, Any] = {'school_id': sid, 'status': 'success'}
    if start_date or end_date:
        rq: Dict[str, Any] = {}
        if start_date:
            rq['$gte'] = start_date
        if end_date:
            rq['$lte'] = end_date + 'T23:59:59'
        q['paid_at'] = rq
    payments = await payments_col.find(q, {'_id': 0}).sort('paid_at', -1).to_list(5000)
    total = sum(p.get('total_paid', 0) for p in payments)
    by_mode: Dict[str, float] = {}
    for p in payments:
        m = p.get('payment_mode', 'cash')
        by_mode[m] = by_mode.get(m, 0) + p.get('total_paid', 0)
    return {'payments': payments, 'total': total, 'by_mode': by_mode, 'count': len(payments)}


@api.get('/reports/collection.pdf')
async def report_collection_pdf(request: Request, current=Depends(get_current_user),
                                school_id: Optional[str] = None,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None):
    data = await report_collection(request, current, school_id, start_date, end_date)
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    school = await schools_col.find_one({'id': sid}, {'_id': 0}) or {}
    cols = ['Receipt No', 'Date', 'Student', 'Mode', 'Amount (Rs.)']
    rows = []
    for p in data['payments']:
        rows.append([p.get('receipt_number', ''),
                     (p.get('paid_at') or '')[:10],
                     p.get('student_name', ''),
                     str(p.get('payment_mode', '')).replace('_', ' ').title(),
                     f"{p.get('total_paid', 0):,.2f}"])
    subtitle = f"Period: {start_date or 'All'}  to  {end_date or 'Today'}"
    summary = {'Total Collection': f"Rs. {data['total']:,.2f}", 'Transactions': data['count']}
    pdf = generate_report_pdf('Fee Collection Report', subtitle, cols, rows,
                              school.get('name', 'Stanvard School'), summary)
    return StreamingResponse(io.BytesIO(pdf), media_type='application/pdf',
                             headers={'Content-Disposition': 'inline; filename="collection_report.pdf"'})


@api.get('/reports/collection.csv')
async def report_collection_csv(request: Request, current=Depends(get_current_user),
                                school_id: Optional[str] = None,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None):
    data = await report_collection(request, current, school_id, start_date, end_date)
    import csv
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Receipt No', 'Date', 'Student', 'Mode', 'Amount'])
    for p in data['payments']:
        writer.writerow([p.get('receipt_number', ''),
                        (p.get('paid_at') or '')[:10],
                        p.get('student_name', ''),
                        p.get('payment_mode', ''),
                        p.get('total_paid', 0)])
    return StreamingResponse(io.BytesIO(buffer.getvalue().encode()),
                             media_type='text/csv',
                             headers={'Content-Disposition': 'attachment; filename="collection.csv"'})


@api.get('/reports/collection.xlsx')
async def report_collection_xlsx(request: Request, current=Depends(get_current_user),
                                 school_id: Optional[str] = None,
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None):
    from openpyxl import Workbook
    data = await report_collection(request, current, school_id, start_date, end_date)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Collection'
    ws.append(['Receipt No', 'Date', 'Student', 'Mode', 'Amount'])
    for p in data['payments']:
        ws.append([p.get('receipt_number', ''),
                   (p.get('paid_at') or '')[:10],
                   p.get('student_name', ''),
                   p.get('payment_mode', ''),
                   p.get('total_paid', 0)])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers={'Content-Disposition': 'attachment; filename="collection.xlsx"'})


@api.get('/reports/attendance')
async def report_attendance(request: Request, current=Depends(get_current_user),
                            school_id: Optional[str] = None,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            class_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    q: Dict[str, Any] = {'school_id': sid}
    if start_date or end_date:
        rq: Dict[str, Any] = {}
        if start_date:
            rq['$gte'] = start_date
        if end_date:
            rq['$lte'] = end_date
        q['date'] = rq
    if class_id:
        q['class_id'] = class_id
    rows = await attendance_col.find(q, {'_id': 0}).to_list(20000)
    total = len(rows)
    present = sum(1 for r in rows if r.get('status') == 'present')
    absent = sum(1 for r in rows if r.get('status') == 'absent')
    leave = sum(1 for r in rows if r.get('status') == 'leave')
    return {'total': total, 'present': present, 'absent': absent, 'leave': leave,
            'attendance_rate': round(present / total * 100, 2) if total else 0.0}


# =====================================================
# DASHBOARD
# =====================================================
@api.get('/dashboard/summary')
async def dashboard_summary(request: Request, current=Depends(get_current_user),
                            school_id: Optional[str] = None):
    sid = await resolve_school_id_safe(current, school_id, request.headers.get('X-School-Id'))
    today = datetime.now().strftime('%Y-%m-%d')
    month_start = datetime.now().strftime('%Y-%m-01')

    total_students = await students_col.count_documents({'school_id': sid, 'status': 'active'})
    total_staff = await staff_col.count_documents({'school_id': sid, 'status': 'active'})

    # Today's collection
    today_payments = await payments_col.find({'school_id': sid, 'paid_at': {'$gte': today, '$lt': today + 'T23:59:59'}}, {'_id': 0}).to_list(2000)
    today_collection = sum(p.get('total_paid', 0) for p in today_payments)
    # Monthly collection
    month_payments = await payments_col.find({'school_id': sid, 'paid_at': {'$gte': month_start}}, {'_id': 0}).to_list(5000)
    monthly_collection = sum(p.get('total_paid', 0) for p in month_payments)

    # Attendance today
    today_att = await attendance_col.find({'school_id': sid, 'date': today}, {'_id': 0}).to_list(5000)
    present_today = sum(1 for a in today_att if a.get('status') == 'present')
    absent_today = sum(1 for a in today_att if a.get('status') == 'absent')

    # New admissions (this month)
    new_admissions = await students_col.count_documents({
        'school_id': sid,
        'created_at': {'$gte': month_start}
    })

    # Recent activity
    recent_payments = await payments_col.find({'school_id': sid}, {'_id': 0}).sort('paid_at', -1).limit(5).to_list(5)
    upcoming_events = await events_col.find({
        'school_id': sid, 'event_date': {'$gte': today}
    }, {'_id': 0}).sort('event_date', 1).limit(5).to_list(5)
    recent_circulars = await circulars_col.find({
        'school_id': sid, 'status': 'published'
    }, {'_id': 0}).sort('created_at', -1).limit(5).to_list(5)

    # Pending fees (naive: students with assignments who haven't paid this month)
    with_assignments = await fee_assignments_col.distinct('student_id', {'school_id': sid})
    paid_this_month = await payments_col.distinct('student_id', {'school_id': sid, 'paid_at': {'$gte': month_start}})
    pending_students = max(len(with_assignments) - len(paid_this_month), 0)

    # Collection trend last 7 days
    trend = []
    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        payments = await payments_col.find({'school_id': sid, 'paid_at': {'$gte': d, '$lt': d + 'T23:59:59'}}, {'_id': 0}).to_list(1000)
        trend.append({'date': d, 'amount': sum(p.get('total_paid', 0) for p in payments)})

    return {
        'total_students': total_students,
        'total_staff': total_staff,
        'today_collection': today_collection,
        'monthly_collection': monthly_collection,
        'present_today': present_today,
        'absent_today': absent_today,
        'new_admissions': new_admissions,
        'pending_students': pending_students,
        'recent_payments': recent_payments,
        'upcoming_events': upcoming_events,
        'recent_circulars': recent_circulars,
        'collection_trend': trend,
    }


# =====================================================
# AUDIT LOGS
# =====================================================
@api.get('/audit-logs', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def list_audit(request: Request, current=Depends(get_current_user),
                    school_id: Optional[str] = None, limit: int = 200):
    q: Dict[str, Any] = {}
    if current['role'] == 'super_admin':
        if school_id:
            q['school_id'] = school_id
    else:
        q['school_id'] = current['school_id']
    rows = await audit_col.find(q, {'_id': 0}).sort('created_at', -1).limit(limit).to_list(limit)
    return rows


# =====================================================
# SETTINGS
# =====================================================
@api.get('/settings')
async def get_settings(request: Request, current=Depends(get_current_user), school_id: Optional[str] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    s = await settings_col.find_one({'school_id': sid}, {'_id': 0})
    if not s:
        s = SchoolSettings(school_id=sid).model_dump()
        await settings_col.insert_one(dict(s))
        s = await settings_col.find_one({'school_id': sid}, {'_id': 0})
    return s


@api.patch('/settings', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def update_settings(payload: Dict[str, Any], request: Request, current=Depends(get_current_user)):
    sid = resolve_school_id(current, None, request.headers.get('X-School-Id'))
    payload['updated_at'] = now_iso()
    await settings_col.update_one({'school_id': sid}, {'$set': payload}, upsert=True)
    await log_audit(action='settings.update', current_user=current, school_id=sid,
                    entity_type='settings', details=payload)
    return await settings_col.find_one({'school_id': sid}, {'_id': 0})


# =====================================================
# USER DELETE + PASSWORD RESET
# =====================================================
@api.delete('/users/{user_id}', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def delete_user(user_id: str, current=Depends(get_current_user)):
    target = await users_col.find_one({'id': user_id}, {'_id': 0})
    if not target:
        raise HTTPException(404, 'User not found')
    if current['role'] == 'school_admin':
        if target.get('school_id') != current.get('school_id') or target.get('role') == 'super_admin':
            raise HTTPException(403, 'Cannot delete this user')
    if target['id'] == current['id']:
        raise HTTPException(400, 'Cannot delete yourself')
    await users_col.update_one({'id': user_id}, {'$set': {'status': 'inactive', 'updated_at': now_iso()}})
    await log_audit(action='user.delete', current_user=current,
                    entity_type='user', entity_id=user_id, details={'email': target.get('email')})
    return {'ok': True}


@api.post('/users/{user_id}/reset-password', dependencies=[Depends(require_roles('super_admin', 'school_admin'))])
async def reset_password(user_id: str, payload: Dict[str, str], current=Depends(get_current_user)):
    new_pw = payload.get('password')
    if not new_pw or len(new_pw) < 6:
        raise HTTPException(400, 'Password must be at least 6 characters')
    target = await users_col.find_one({'id': user_id}, {'_id': 0})
    if not target:
        raise HTTPException(404, 'User not found')
    if current['role'] == 'school_admin' and target.get('school_id') != current.get('school_id'):
        raise HTTPException(403, 'Forbidden')
    await users_col.update_one({'id': user_id}, {'$set': {'password_hash': hash_password(new_pw), 'updated_at': now_iso()}})
    await log_audit(action='user.reset_password', current_user=current,
                    entity_type='user', entity_id=user_id, details={'email': target.get('email')})
    return {'ok': True}


# =====================================================
# ANALYTICS
# =====================================================
@api.get('/analytics')
async def analytics(request: Request, current=Depends(get_current_user),
                   school_id: Optional[str] = None, year: Optional[int] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    year = year or datetime.now().year
    year_start = f'{year}-01-01'
    year_end = f'{year}-12-31T23:59:59'

    # All payments for the year
    payments = await payments_col.find({
        'school_id': sid, 'status': 'success',
        'paid_at': {'$gte': year_start, '$lte': year_end}
    }, {'_id': 0}).to_list(20000)

    # Monthly breakdown (Jan..Dec)
    months = [{'month': datetime(year, m, 1).strftime('%b'),
               'received': 0.0, 'transactions': 0, 'discount': 0.0, 'late_fee': 0.0}
              for m in range(1, 13)]
    by_mode = {}
    by_head = {}
    for p in payments:
        try:
            paid_month = int((p.get('paid_at') or '')[5:7])
            months[paid_month - 1]['received'] += p.get('total_paid', 0)
            months[paid_month - 1]['transactions'] += 1
            months[paid_month - 1]['discount'] += p.get('discount', 0)
            months[paid_month - 1]['late_fee'] += p.get('late_fee', 0)
        except Exception:
            pass
        mode = p.get('payment_mode', 'cash')
        by_mode[mode] = by_mode.get(mode, 0) + p.get('total_paid', 0)
        for item in p.get('items', []):
            hd = item.get('fee_head_name', 'Other')
            by_head[hd] = by_head.get(hd, 0) + item.get('amount', 0)

    total_received = sum(p.get('total_paid', 0) for p in payments)
    total_transactions = len(payments)
    total_discount = sum(p.get('discount', 0) for p in payments)
    total_late_fee = sum(p.get('late_fee', 0) for p in payments)

    # Expected: sum of all assignment amounts (custom_items or plan)
    assignments = await fee_assignments_col.find({'school_id': sid}, {'_id': 0}).to_list(10000)
    total_expected = 0.0
    plans_cache: Dict[str, Any] = {}
    for a in assignments:
        items = a.get('custom_items') or []
        if not items and a.get('fee_plan_id'):
            pid = a['fee_plan_id']
            if pid not in plans_cache:
                plans_cache[pid] = await fee_plans_col.find_one({'id': pid}, {'_id': 0}) or {}
            items = plans_cache[pid].get('items', [])
        for it in items:
            total_expected += it.get('amount', 0)
        total_expected -= a.get('discount_amount', 0)
    total_due = max(total_expected - total_received, 0)

    # Attendance summary for the year
    att = await attendance_col.find({'school_id': sid, 'date': {'$gte': year_start[:10], '$lte': year_end[:10]}}, {'_id': 0}).to_list(50000)
    att_total = len(att)
    att_present = sum(1 for a in att if a.get('status') == 'present')
    att_absent = sum(1 for a in att if a.get('status') == 'absent')
    att_leave = sum(1 for a in att if a.get('status') == 'leave')

    # New admissions per month
    students = await students_col.find({'school_id': sid}, {'_id': 0}).to_list(5000)
    adm_months = [0] * 12
    for s in students:
        try:
            ca = s.get('created_at') or s.get('admission_date') or ''
            if ca and int(ca[:4]) == year:
                adm_months[int(ca[5:7]) - 1] += 1
        except Exception:
            pass
    for i, m in enumerate(months):
        m['admissions'] = adm_months[i]

    # Class-wise pending (approximation)
    classes = await classes_col.find({'school_id': sid}, {'_id': 0}).to_list(200)
    by_class = []
    for c in classes:
        students_in_class = [s for s in students if s.get('class_id') == c['id']]
        payer_ids = {p['student_id'] for p in payments if p['student_id'] in {s['id'] for s in students_in_class}}
        by_class.append({
            'class_id': c['id'], 'class_name': c['name'],
            'total_students': len(students_in_class),
            'paying_students': len(payer_ids),
            'pending_students': max(len(students_in_class) - len(payer_ids), 0),
        })

    return {
        'year': year,
        'total_received': total_received,
        'total_expected': total_expected,
        'total_due': total_due,
        'total_discount': total_discount,
        'total_late_fee': total_late_fee,
        'total_transactions': total_transactions,
        'months': months,
        'by_mode': by_mode,
        'by_head': by_head,
        'by_class': by_class,
        'attendance': {
            'total': att_total,
            'present': att_present,
            'absent': att_absent,
            'leave': att_leave,
            'rate': round(att_present / att_total * 100, 2) if att_total else 0.0,
        },
        'total_students': len(students),
    }


# =====================================================
# ENHANCED REPORTS - Fee Status per student (paid/pending)
# =====================================================
@api.get('/reports/fee-status')
async def report_fee_status(request: Request, current=Depends(get_current_user),
                            school_id: Optional[str] = None,
                            class_id: Optional[str] = None,
                            section: Optional[str] = None,
                            status_filter: Optional[str] = None,  # paid|partial|unpaid
                            min_due: Optional[float] = None,
                            max_due: Optional[float] = None):
    sid = resolve_school_id(current, school_id, request.headers.get('X-School-Id'))
    student_q: Dict[str, Any] = {'school_id': sid, 'status': 'active'}
    if class_id:
        student_q['class_id'] = class_id
    if section:
        student_q['section'] = section
    students = await students_col.find(student_q, {'_id': 0}).to_list(5000)

    # Build class map
    classes = await classes_col.find({'school_id': sid}, {'_id': 0}).to_list(200)
    class_map = {c['id']: c['name'] for c in classes}

    # Get all assignments & payments in bulk
    student_ids = [s['id'] for s in students]
    assignments = await fee_assignments_col.find({'student_id': {'$in': student_ids}}, {'_id': 0}).to_list(20000)
    payments = await payments_col.find({'student_id': {'$in': student_ids}, 'status': 'success'}, {'_id': 0}).to_list(20000)

    # Plan cache
    plan_cache: Dict[str, Any] = {}
    async def _get_plan(pid):
        if pid not in plan_cache:
            plan_cache[pid] = await fee_plans_col.find_one({'id': pid}, {'_id': 0}) or {}
        return plan_cache[pid]

    # Sum per student
    expected_by_stu: Dict[str, float] = {}
    discount_by_stu: Dict[str, float] = {}
    due_date_by_stu: Dict[str, Optional[str]] = {}
    for a in assignments:
        sid_ = a['student_id']
        items = a.get('custom_items') or []
        if not items and a.get('fee_plan_id'):
            plan = await _get_plan(a['fee_plan_id'])
            items = plan.get('items', [])
        expected_by_stu[sid_] = expected_by_stu.get(sid_, 0.0) + sum(i.get('amount', 0) for i in items)
        discount_by_stu[sid_] = discount_by_stu.get(sid_, 0.0) + a.get('discount_amount', 0)
        if a.get('due_date') and not due_date_by_stu.get(sid_):
            due_date_by_stu[sid_] = a['due_date']

    paid_by_stu: Dict[str, float] = {}
    for p in payments:
        paid_by_stu[p['student_id']] = paid_by_stu.get(p['student_id'], 0.0) + p.get('total_paid', 0)

    rows = []
    for s in students:
        expected = expected_by_stu.get(s['id'], 0.0)
        disc = discount_by_stu.get(s['id'], 0.0)
        paid = paid_by_stu.get(s['id'], 0.0)
        due = max(expected - disc - paid, 0.0)
        row_status = 'unpaid' if paid == 0 else ('paid' if due <= 0 else 'partial')
        if status_filter and status_filter != row_status:
            continue
        if min_due is not None and due < min_due:
            continue
        if max_due is not None and due > max_due:
            continue
        rows.append({
            'student_id': s['id'],
            'admission_number': s.get('admission_number'),
            'full_name': s.get('full_name'),
            'class_name': class_map.get(s.get('class_id'), '-'),
            'section': s.get('section'),
            'phone': s.get('phone'),
            'father_name': s.get('father_name'),
            'expected': expected,
            'discount': disc,
            'paid': paid,
            'due': due,
            'due_date': due_date_by_stu.get(s['id']),
            'status': row_status,
        })
    total_expected = sum(r['expected'] for r in rows)
    total_paid = sum(r['paid'] for r in rows)
    total_due = sum(r['due'] for r in rows)
    total_discount = sum(r['discount'] for r in rows)
    return {
        'rows': rows,
        'count': len(rows),
        'summary': {
            'total_expected': total_expected,
            'total_paid': total_paid,
            'total_due': total_due,
            'total_discount': total_discount,
            'paid_count': sum(1 for r in rows if r['status'] == 'paid'),
            'partial_count': sum(1 for r in rows if r['status'] == 'partial'),
            'unpaid_count': sum(1 for r in rows if r['status'] == 'unpaid'),
        }
    }


# ------------ Mount router & middlewares ------------
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup():
    # Create indexes
    await users_col.create_index('email', unique=True)
    await students_col.create_index([('school_id', 1), ('admission_number', 1)])
    await students_col.create_index([('school_id', 1), ('class_id', 1)])
    await payments_col.create_index([('school_id', 1), ('paid_at', -1)])
    await attendance_col.create_index([('school_id', 1), ('date', 1), ('class_id', 1)])
    logger.info('Stanvard ERP API started')


@app.on_event('shutdown')
async def shutdown():
    mongo_client.close()
