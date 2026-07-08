"""Pydantic models for Stanvard School ERP."""
from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone
import uuid


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


class BaseDoc(BaseModel):
    model_config = ConfigDict(extra='ignore', populate_by_name=True)
    id: str = Field(default_factory=new_id)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


# ---------- SCHOOL ----------
class School(BaseDoc):
    name: str
    code: str  # short code e.g. GN, KNP, AYR
    city: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    principal_name: Optional[str] = None
    logo_url: Optional[str] = None
    academic_session: str = '2025-26'
    status: str = 'active'  # active | archived


class SchoolCreate(BaseModel):
    name: str
    code: str
    city: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    principal_name: Optional[str] = None
    academic_session: str = '2025-26'


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    principal_name: Optional[str] = None
    logo_url: Optional[str] = None
    academic_session: Optional[str] = None
    status: Optional[str] = None


# ---------- USER / AUTH ----------
ROLES = {'super_admin', 'school_admin', 'accountant', 'teacher', 'parent'}


class User(BaseDoc):
    email: EmailStr
    password_hash: str
    full_name: str
    role: str  # super_admin|school_admin|accountant|teacher|parent
    school_id: Optional[str] = None  # None for super_admin
    phone: Optional[str] = None
    linked_student_id: Optional[str] = None  # for parent role
    linked_class_ids: List[str] = Field(default_factory=list)  # for teacher
    status: str = 'active'


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    school_id: Optional[str] = None
    phone: Optional[str] = None
    linked_student_id: Optional[str] = None
    linked_class_ids: List[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    school_id: Optional[str] = None
    phone: Optional[str] = None
    linked_student_id: Optional[str] = None
    linked_class_ids: Optional[List[str]] = None
    status: Optional[str] = None
    password: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: Dict[str, Any]


# ---------- STUDENT ----------
class Student(BaseDoc):
    school_id: str
    admission_number: str
    roll_number: Optional[str] = None
    full_name: str
    dob: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    religion: Optional[str] = None
    category: Optional[str] = None
    class_id: Optional[str] = None
    section: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    transport_route: Optional[str] = None
    medical_info: Optional[str] = None
    previous_school: Optional[str] = None
    scholarship: Optional[str] = None
    fee_category: Optional[str] = None
    photo_url: Optional[str] = None
    documents: List[Dict[str, str]] = Field(default_factory=list)
    remarks: Optional[str] = None
    admission_date: Optional[str] = None
    status: str = 'active'


class StudentCreate(BaseModel):
    school_id: Optional[str] = None  # inferred from user context
    admission_number: Optional[str] = None  # auto-gen if empty
    roll_number: Optional[str] = None
    full_name: str
    dob: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    religion: Optional[str] = None
    category: Optional[str] = None
    class_id: Optional[str] = None
    section: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    transport_route: Optional[str] = None
    medical_info: Optional[str] = None
    previous_school: Optional[str] = None
    scholarship: Optional[str] = None
    fee_category: Optional[str] = None
    photo_url: Optional[str] = None
    remarks: Optional[str] = None
    admission_date: Optional[str] = None


class StudentUpdate(BaseModel):
    admission_number: Optional[str] = None
    roll_number: Optional[str] = None
    full_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    religion: Optional[str] = None
    category: Optional[str] = None
    class_id: Optional[str] = None
    section: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    transport_route: Optional[str] = None
    medical_info: Optional[str] = None
    previous_school: Optional[str] = None
    scholarship: Optional[str] = None
    fee_category: Optional[str] = None
    photo_url: Optional[str] = None
    remarks: Optional[str] = None
    admission_date: Optional[str] = None
    status: Optional[str] = None


# ---------- CLASS ----------
class ClassRoom(BaseDoc):
    school_id: str
    name: str  # e.g. Class VIII
    sections: List[str] = Field(default_factory=list)  # ['A','B','C']
    teacher_id: Optional[str] = None


class ClassCreate(BaseModel):
    school_id: Optional[str] = None
    name: str
    sections: List[str] = Field(default_factory=list)
    teacher_id: Optional[str] = None


# ---------- FEE ----------
class FeeHead(BaseDoc):
    school_id: str
    name: str  # Tuition, Transport, etc.
    category: str = 'general'  # general|transport|hostel|exam|activity
    is_active: bool = True


class FeeHeadCreate(BaseModel):
    school_id: Optional[str] = None
    name: str
    category: str = 'general'


class FeePlanItem(BaseModel):
    fee_head_id: str
    fee_head_name: str
    amount: float
    frequency: str = 'monthly'  # monthly|quarterly|half_yearly|yearly|one_time
    installments: int = 12  # for monthly=12, quarterly=4, half_yearly=2, yearly=1


class FeePlan(BaseDoc):
    school_id: str
    name: str  # e.g. 'Class VIII 2025-26'
    academic_session: str = '2025-26'
    class_id: Optional[str] = None  # if class-wide plan
    items: List[FeePlanItem] = Field(default_factory=list)
    annual_discount_percent: float = 0.0  # early payment discount %
    late_fee_amount: float = 0.0
    late_fee_after_day: int = 10  # apply late fee after day X of month
    is_active: bool = True


class FeePlanCreate(BaseModel):
    school_id: Optional[str] = None
    name: str
    academic_session: str = '2025-26'
    class_id: Optional[str] = None
    items: List[FeePlanItem] = Field(default_factory=list)
    annual_discount_percent: float = 0.0
    late_fee_amount: float = 0.0
    late_fee_after_day: int = 10


class FeeAssignment(BaseDoc):
    school_id: str
    student_id: str
    fee_plan_id: str
    academic_session: str = '2025-26'
    custom_amount: Optional[float] = None  # override plan
    discount_percent: Optional[float] = None
    remarks: Optional[str] = None


class FeeAssignmentCreate(BaseModel):
    school_id: Optional[str] = None
    student_id: str
    fee_plan_id: str
    academic_session: str = '2025-26'
    custom_amount: Optional[float] = None
    discount_percent: Optional[float] = None
    remarks: Optional[str] = None


# ---------- PAYMENT / RECEIPT ----------
class PaymentLineItem(BaseModel):
    fee_head_id: Optional[str] = None
    fee_head_name: str
    period: str = ''  # e.g. 'October 2025' or 'Annual'
    amount: float


class Payment(BaseDoc):
    school_id: str
    student_id: str
    student_name: str = ''
    receipt_number: str = ''
    items: List[PaymentLineItem] = Field(default_factory=list)
    subtotal: float = 0.0
    discount: float = 0.0
    late_fee: float = 0.0
    total_paid: float = 0.0
    payment_mode: str = 'cash'  # cash|upi|card|cheque|bank_transfer|razorpay
    txn_ref: Optional[str] = None  # UPI ref / cheque no / bank txn / razorpay payment id
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    status: str = 'success'  # success|pending|refunded|failed
    remarks: Optional[str] = None
    collected_by_id: Optional[str] = None
    collected_by_name: Optional[str] = None
    paid_at: str = Field(default_factory=now_iso)


class PaymentCreate(BaseModel):
    school_id: Optional[str] = None
    student_id: str
    items: List[PaymentLineItem]
    discount: float = 0.0
    late_fee: float = 0.0
    payment_mode: str = 'cash'
    txn_ref: Optional[str] = None
    remarks: Optional[str] = None


class RazorpayOrderRequest(BaseModel):
    student_id: str
    items: List[PaymentLineItem]
    discount: float = 0.0
    late_fee: float = 0.0
    remarks: Optional[str] = None


class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# ---------- ATTENDANCE ----------
class AttendanceRecord(BaseDoc):
    school_id: str
    date: str  # YYYY-MM-DD
    class_id: str
    section: Optional[str] = None
    student_id: str
    status: str = 'present'  # present|absent|leave
    remarks: Optional[str] = None
    marked_by_id: Optional[str] = None


class AttendanceBulkMark(BaseModel):
    school_id: Optional[str] = None
    date: str
    class_id: str
    section: Optional[str] = None
    entries: List[Dict[str, str]]  # [{student_id, status, remarks?}]


# ---------- HOMEWORK ----------
class Homework(BaseDoc):
    school_id: str
    class_id: str
    section: Optional[str] = None
    subject: str
    title: str
    description: str
    due_date: Optional[str] = None
    attachment_url: Optional[str] = None
    created_by_id: Optional[str] = None
    created_by_name: Optional[str] = None


class HomeworkCreate(BaseModel):
    school_id: Optional[str] = None
    class_id: str
    section: Optional[str] = None
    subject: str
    title: str
    description: str
    due_date: Optional[str] = None
    attachment_url: Optional[str] = None


# ---------- TIMETABLE ----------
class TimetableSlot(BaseModel):
    day: str  # Monday..Saturday
    period: int  # 1..8
    start_time: str  # '09:00'
    end_time: str  # '09:45'
    subject: str
    teacher_name: Optional[str] = None


class Timetable(BaseDoc):
    school_id: str
    class_id: str
    section: Optional[str] = None
    slots: List[TimetableSlot] = Field(default_factory=list)


class TimetableCreate(BaseModel):
    school_id: Optional[str] = None
    class_id: str
    section: Optional[str] = None
    slots: List[TimetableSlot]


# ---------- EVENT ----------
class Event(BaseDoc):
    school_id: str
    title: str
    description: Optional[str] = None
    event_date: str  # YYYY-MM-DD
    location: Optional[str] = None
    image_url: Optional[str] = None
    status: str = 'upcoming'  # upcoming|past


class EventCreate(BaseModel):
    school_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    event_date: str
    location: Optional[str] = None
    image_url: Optional[str] = None


# ---------- CIRCULAR ----------
class Circular(BaseDoc):
    school_id: str
    title: str
    body: str
    priority: str = 'normal'  # low|normal|high|urgent
    status: str = 'published'  # draft|scheduled|published
    publish_at: Optional[str] = None
    attachment_url: Optional[str] = None
    audience: str = 'all'  # all|teachers|parents|students|class
    class_id: Optional[str] = None
    created_by_name: Optional[str] = None


class CircularCreate(BaseModel):
    school_id: Optional[str] = None
    title: str
    body: str
    priority: str = 'normal'
    status: str = 'published'
    publish_at: Optional[str] = None
    attachment_url: Optional[str] = None
    audience: str = 'all'
    class_id: Optional[str] = None


# ---------- GALLERY ----------
class GalleryAlbum(BaseDoc):
    school_id: str
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    photos: List[str] = Field(default_factory=list)  # image URLs


class GalleryAlbumCreate(BaseModel):
    school_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    photos: List[str] = Field(default_factory=list)


# ---------- STAFF ----------
class Staff(BaseDoc):
    school_id: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    designation: str  # Teacher|Principal|Accountant|Clerk
    department: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    joining_date: Optional[str] = None
    photo_url: Optional[str] = None
    status: str = 'active'


class StaffCreate(BaseModel):
    school_id: Optional[str] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    designation: str
    department: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    joining_date: Optional[str] = None
    photo_url: Optional[str] = None


# ---------- NOTIFICATION ----------
class Notification(BaseDoc):
    school_id: str
    title: str
    body: str
    audience: str = 'all'  # all|teachers|parents|class|student
    class_id: Optional[str] = None
    student_ids: List[str] = Field(default_factory=list)
    kind: str = 'announcement'  # announcement|homework|fee_reminder|exam|emergency
    read_by: List[str] = Field(default_factory=list)


class NotificationCreate(BaseModel):
    school_id: Optional[str] = None
    title: str
    body: str
    audience: str = 'all'
    class_id: Optional[str] = None
    student_ids: List[str] = Field(default_factory=list)
    kind: str = 'announcement'


# ---------- AUDIT ----------
class AuditLog(BaseDoc):
    school_id: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    role: Optional[str] = None
    action: str  # e.g. 'student.create', 'payment.collect'
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None


# ---------- SETTINGS ----------
class SchoolSettings(BaseDoc):
    school_id: str
    theme: str = 'default'
    receipt_template: Dict[str, Any] = Field(default_factory=dict)
    late_fee_rules: Dict[str, Any] = Field(default_factory=dict)
    discount_rules: Dict[str, Any] = Field(default_factory=dict)
