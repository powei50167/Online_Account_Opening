from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict
from pydantic import BaseModel
from online_account_opening.core.database_connection import SessionLocal
from datetime import datetime
from online_account_opening.core.logger_module import LoggerManager

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 對應回傳的英文欄位（前端格式）
class InboundOut(BaseModel):
    record_date: str
    case_id: str
    register_date: Optional[str]
    customer_name: Optional[str]
    phone: Optional[str]
    sales: Optional[str]
    assigned_sales: Optional[str]
    mail_status: str 
    notes: Optional[str]

    class Config:
        from_attributes  = True

@router.get("/inbounds", response_model=List[InboundOut])
def read_inbounds(date: Optional[str] = None, db: Session = Depends(get_db)):
    sql = text("""
            SELECT 
                i1.*,
                i2.`指派營業員` AS `歷史指派營業員`,
                mt.寄件時間,
                mt.回覆時間,
                List_Type.type,
                i3.note
            FROM 
                `Account Opening`.Inbound_list i1
            LEFT JOIN (
                SELECT t.*
                FROM (
                    SELECT *,
                        ROW_NUMBER() OVER (PARTITION BY 案件編號 ORDER BY STR_TO_DATE(`紀錄日期`, '%Y/%c/%e') DESC) AS rn
                    FROM `Account Opening`.Inbound_list
                    WHERE `指派營業員` IS NOT NULL
                ) t
                WHERE t.rn = 1
            ) i2
            ON i1.`案件編號` = i2.`案件編號`
            LEFT JOIN (
                SELECT *
                FROM (
                    SELECT *,
                        ROW_NUMBER() OVER (PARTITION BY 案件編號 ORDER BY 寄件日期 DESC, mail_id DESC) AS rn
                    FROM `Account Opening`.Mail_Tracking where 寄件日期 is not null
                ) t
                WHERE t.rn = 1
            ) mt ON i1.`案件編號` = mt.`案件編號`
            left join
	            List_Type On  mt.項目 = List_Type.index
            LEFT JOIN (
                SELECT t.*
                FROM (
                    SELECT *,
                        ROW_NUMBER() OVER (PARTITION BY case_number ORDER BY created_at  DESC) AS rn
                    FROM `Account Opening`.Inbound_list_notes
                    WHERE `note` IS NOT NULL
                ) t
                WHERE t.rn = 1
            ) i3
            ON i1.`案件編號` = i3.`case_number`
            WHERE 
                STR_TO_DATE(i1.`紀錄日期`, '%Y/%c/%e') = STR_TO_DATE(:date, '%Y-%m-%d')
            ORDER BY 
                STR_TO_DATE(i1.`登錄日期`, '%Y/%m/%d') DESC;
    """)
    result = db.execute(sql, {"date": date}).mappings().fetchall()

    def format_assigned_sales(value):
        if value is None :
            return "無"
        return value
    
    return [
        {
            "record_date": row["紀錄日期"],
            "case_id": row["案件編號"],
            "register_date": row["登錄日期"],
            "customer_name": row["客戶名稱"],
            "phone": row["手機號碼"],
            "sales": row["營業員"],
            "assigned_sales": format_assigned_sales(row["歷史指派營業員"]),
            "mail_status": (
                "未提醒" if row["寄件時間"] is None 
                else 
                "已回覆" if row["回覆時間"] is not None 
                else "待回覆"
            ),
            'notes':format_assigned_sales(row['note'])
        }
        for row in result
    ]

class RecordItem(BaseModel):
    case_id: str
    record_date: str  # 格式為 "2025/4/2"

class AssignRequest(BaseModel):
    records: List[RecordItem]
    sales: str

@router.post("/inbounds/assign")
def assign_sales(req: AssignRequest, db: Session = Depends(get_db)):
    for record in req.records:
        sql = text("""
            UPDATE `Account Opening`.Inbound_list
            SET `指派營業員` = :sales
            WHERE `案件編號` = :case_id
              AND STR_TO_DATE(`紀錄日期`, '%Y/%c/%e') = STR_TO_DATE(:record_date, '%Y-%m-%d')
        """)
        db.execute(sql, {
            "sales": req.sales,
            "case_id": record.case_id,
            "record_date": record.record_date
        })

    db.commit()
    return {"message": "success"}

class OrgItem(BaseModel):
    employee_id: str
    name: str
    email: Optional[str]
    supervisor_id: Optional[str]
    supervisor_name: Optional[str]
    dept_code: Optional[str]
    dept_name: Optional[str]

@router.get("/organization", response_model=List[OrgItem])
def get_organization(db: Session = Depends(get_db)):
    sql = text("SELECT * FROM pfcf.Organizational_VIEW where 部門 like '%期貨%' order by 部門")
    result = db.execute(sql).mappings().fetchall()
    
    return [
        {
            "employee_id": row["員編"],
            "name": row["姓名"],
            "email": row["信箱"],
            "supervisor_id": row["主管員鯿"],
            "supervisor_name": row["主管"],
            "dept_code": row["部門代碼"],
            "dept_name": row["部門"]
        }
        for row in result
    ]

class branch_incomplete_Out(BaseModel):
    record_date: str
    register_date: str
    branch: str
    case_id: str
    last_return_time: Optional[str]
    customer_name: str
    phone: str
    sales: str
    status: str
    mail_status: str
    inputdate: str
    notes: Optional[str]

def is_valid_datetime(dt_str: Optional[str]) -> bool:
    if not dt_str or dt_str.strip().lower() == "nat":
        return False
    try:
        datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False
    
@router.get("/branch_incomplete", response_model=List[branch_incomplete_Out])
def read_branch_incomplete(date: Optional[str] = None, branch: Optional[str] = None, db: Session = Depends(get_db)):
    sql = text("""
        SELECT 
            r.紀錄日期,
            r.未完成名單,
            r.進件日期,
            r.分公司,
            r.案件編號,
            r.最後退補件時間,
            r.客戶姓名,
            r.手機號碼,
            r.營業員,
            r.匯入時間,
            mt.寄件時間,
            mt.回覆時間,
            List_Type.type,
            i3.note
        FROM (
            SELECT 
                日期 as 紀錄日期,
                未完成名單,
                進件日期,
                分公司,
                案件編號,
                最後退補件時間,
                客戶姓名,
                手機號碼,
                營業員,
                匯入時間,
                ROW_NUMBER() OVER (PARTITION BY 案件編號 ORDER BY STR_TO_DATE(匯入時間, '%Y-%m-%d %H:%i:%s') DESC) AS rn
            FROM `Account Opening`.Reminder_List
            WHERE 
                STR_TO_DATE(`日期`, '%Y%c%e') = STR_TO_DATE(:date, '%Y-%m-%d') 
                AND 分公司 = :branch
        ) r
        LEFT JOIN (
            SELECT *
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (PARTITION BY 案件編號 ORDER BY 寄件日期 DESC, mail_id DESC) AS rn
                FROM `Account Opening`.Mail_Tracking where 寄件日期 is not null and 項目 <> 3
            ) t
            WHERE t.rn = 1
        ) mt ON r.`案件編號` = mt.`案件編號`
        LEFT JOIN (
            SELECT t.*
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (PARTITION BY case_number ORDER BY created_at  DESC) AS rn
                FROM `Account Opening`.Inbound_list_notes
                WHERE `note` IS NOT NULL
            ) t
            WHERE t.rn = 1
        ) i3
        ON r.`案件編號` = i3.`case_number`
        left join
            List_Type On  mt.項目 = List_Type.index
        WHERE r.rn = 1
        ORDER BY STR_TO_DATE(r.最後退補件時間, '%Y-%m-%d %H:%i:%s') DESC;
    """)
    result = db.execute(sql, {"date": date, "branch": branch}).mappings().fetchall()

    def format_last_return_time(value):
        if value is None or str(value).lower() == "nat":
            return "無"
        return value

    return [
        {
            "record_date": row["紀錄日期"],
            "register_date": row["進件日期"],
            "branch": row["分公司"],
            "case_id": row["案件編號"],
            "last_return_time": format_last_return_time(row["最後退補件時間"]),
            "customer_name": row["客戶姓名"],
            "phone": row["手機號碼"],
            "sales": row["營業員"],
            "inputdate": row["匯入時間"],
            "status": (
                "客戶填寫未完成" if row["未完成名單"] is not None and str(row["未完成名單"]).strip() != ""
                else 
                "等待客戶補件" if is_valid_datetime(row["最後退補件時間"])
                else "經辦作業 or AE KYC處理中"
            ),
            "mail_status": (
                "未提醒" if row["寄件時間"] is None 
                else 
                "已回覆" if row["回覆時間"] is not None 
                else "待回覆"
            ),
            'notes':format_last_return_time(row['note'])
        }
        for row in result
    ]

import requests
import json
from dotenv import load_dotenv
import os 

logger = LoggerManager(log_name='email_api', log_file='email_api.log').logger


class EmailRecordItem(BaseModel):
    case_id: str
    record_date: str  # 格式為 "2025/4/2"
    customer_name: str
    phone: str 

class EmailRequest(BaseModel):
    recipient: str
    subject: str
    body: str
    records: List[EmailRecordItem]
    
load_dotenv()

MAIL_API_URL = "http://10.36.205.192:15672/api/exchanges/%2F/pfcf.mail/publish"
MAIL_AUTH_USER = os.getenv("MAIL_AUTH")

@router.post("/send-email")
def send_email(req: EmailRequest, type: str = None, db: Session = Depends(get_db)):
    try:
        logger.info(f"[寄送郵件] 開始處理，主旨: {req.subject}，收件人: {req.recipient}")
        
        for record in req.records:
            # 使用 HTML 表格格式建立內容
            # 合併內容：原本內文 + 表格
            body_content = f"""
                <table width="650" cellpadding="0" cellspacing="0" border="0" style="font-family: Arial, sans-serif; color: #333333;">
                    <tr>
                        <td>
                            <!-- 案件資訊區塊 -->
                            <div style="margin-bottom: 25px;">
                                <h3 style="color: #2c3e50; border-bottom: 2px solid #eaeaea; padding-bottom: 8px; margin-bottom: 15px; text-align: center;">案件資訊</h3>
                                <table width="100%" cellpadding="0" cellspacing="0" border="1" style="border-collapse: collapse; text-align: center; border: 1px solid #dddddd;">
                                    <tr style="background-color: #FFA07A;">
                                        <th style="padding: 10px; border: 1px solid #dddddd;">進件日期</th>
                                        <th style="padding: 10px; border: 1px solid #dddddd;">案件編號</th>
                                        <th style="padding: 10px; border: 1px solid #dddddd;">客戶姓名</th>
                                        <th style="padding: 10px; border: 1px solid #dddddd;">客戶手機</th>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px; border: 1px solid #dddddd;">{record.record_date}</td>
                                        <td style="padding: 10px; border: 1px solid #dddddd;">{record.case_id}</td>
                                        <td style="padding: 10px; border: 1px solid #dddddd;">{record.customer_name}</td>
                                        <td style="padding: 10px; border: 1px solid #dddddd;">{record.phone}</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- 客戶回覆區塊 -->
                            <div style="margin-top: 25px;">
                                <h3 style="color: #2c3e50; border-bottom: 2px solid #eaeaea; padding-bottom: 8px; margin-bottom: 15px; text-align: center;">客戶回覆</h3>
                                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: collapse; text-align: center;">
                                    <tr>
                                        <td style="padding: 10px; height: 150px; background-color: #ffffff; border: 2px solid red;"></td>
                                    </tr>
                                </table>
                                <p style="margin-bottom: 20px; color: red;">{req.body}</p>
                            </div>
                        </td>
                    </tr>
                </table>
            """
            inner_payload = {
                "Subject": f'{req.subject}_{record.case_id}',
                "From": "operation",
                "To": [req.recipient],
                "CC": ["YUANJIN@uni-psg.com","HANHAN07@uni-psg.com"],
                "Bcc": None,
                "Body": body_content,
                "IsBodyHtml": True,
                "Priority": 0,
                "Attachments": None
            }

            body = {
                "properties": {},
                "routing_key": "operation",
                "payload": json.dumps(inner_payload),
                "payload_encoding": "string"
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Basic {MAIL_AUTH_USER}"
            }

            logger.info(f"[寄送請求] body: {json.dumps(body, ensure_ascii=False)}")
            response = requests.post(MAIL_API_URL, json=body, headers=headers)

            if response.ok:
                save_mail_tracking(db, selected_type=type or "未指定", case_id=record.case_id, recipient=req.recipient)
                logger.info(f"[寄送成功] 收件人: {req.recipient}，主旨: {req.subject}")
            else:
                logger.warning(f"[寄送失敗] 收件人: {req.recipient}，狀態碼: {response.status_code}，錯誤內容: {response.text}")
                return {"message": f"寄送失敗，狀態碼 {response.status_code}，內容：{response.text}"}

        return {"message": "已成功寄送所有紀錄"}

    except Exception as e:
        logger.error(f"[例外錯誤] 發送失敗，錯誤訊息: {str(e)}")
        return {"message": "寄送失敗，發生例外錯誤"}

def save_mail_tracking(db: Session, selected_type: str, case_id: str, recipient: str):
    try:
        sql = text("""
            INSERT INTO `Account Opening`.Mail_Tracking (寄件日期, 項目, 案件編號, AE)
            VALUES (:sent_date, :selected_type, :case_id, :recipient)
        """)
        db.execute(sql, {
            "sent_date": datetime.now().date(),
            "selected_type": selected_type,
            "case_id": case_id,
            "recipient": recipient
        })
        db.commit()
        logger.info(f"[追蹤記錄] 儲存成功：{case_id} -> {recipient}")
    except Exception as e:
        db.rollback()
        logger.error(f"[追蹤記錄錯誤] 寫入失敗：{str(e)}")

class EmailContent(BaseModel):
    subject: str
    content: str
 
@router.get("/EmailContent", response_model=List[EmailContent])
def get_email_contents(type: str = None, db: Session = Depends(get_db)):
    sql = text("""
            SELECT 
                subject,
               content
            FROM 
               `Account Opening`.Mail_Content
            WHERE 
               type = :type;
    """)
    result = db.execute(sql, {"type": type}).mappings().fetchall()
    return [
        {
            "subject": row["subject"],
            "content": row["content"]

        }
        for row in result
    ]


from fastapi import HTTPException
from sqlalchemy import text

class LoginResponse(BaseModel):
    username: str
    branch_code: str
    is_admin: bool

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    sql = text("SELECT * FROM `Account Opening`.users WHERE username = :username")
    result = db.execute(sql, {"username": req.username}).mappings().first()

    if not result:
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")

    return {
        "username": result["username"],
        "branch_code": result["branch_code"]
    }

class mail_tracking(BaseModel):
    send_date: datetime
    response_date: Optional[datetime]
    response_ans: Optional[str]
    AE: str
    mail_type: str

@router.get("/get_mail_tracking", response_model=List[mail_tracking])
def read_inbounds(case_id: Optional[str] = None, db: Session = Depends(get_db)):
    sql = text("""
        SELECT 
            寄件時間,
            List_Type.type as mail_type,
            emp.name as AE,
            回覆時間,
            回覆內容 
        FROM 
            `Account Opening`.Mail_Tracking mt
        left join  
            pfcf.employee emp on mt.AE = emp.extension 
        left join
            List_Type On  mt.項目 = List_Type.index
        where 案件編號 =:案件編號;
    """)
    result = db.execute(sql, {"案件編號": case_id}).mappings().fetchall()

  
    return [
        {
            "send_date": row["寄件時間"],
            "response_date": row["回覆時間"],
            "response_ans": row["回覆內容"],
            "AE": row["AE"],
            "mail_type": row["mail_type"]
        }
        for row in result
    ]


class noteRequest(BaseModel):
    records: List[EmailRecordItem]
    note: str  # 新增

@router.post("/edit_note")
def edit_note(req: noteRequest, db: Session = Depends(get_db)):
    try:
        for record in req.records:
            sql = text("""
                INSERT INTO `Account Opening`.Inbound_list_notes
                (case_number, note)
                VALUES (:case_id, :note)
            """)
            db.execute(sql, {
                "case_id": record.case_id,
                "note": req.note
            })

        db.commit()
        logger.info(f"[追蹤記錄] 儲存成功：{record.case_id} -> {req.note}")

    except Exception as e:
        db.rollback()
        logger.error(f"[例外錯誤] 備註編輯失敗，錯誤訊息: {str(e)}")
        return {"message": "備註編輯失敗，發生例外錯誤"}