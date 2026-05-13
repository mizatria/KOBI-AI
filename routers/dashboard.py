import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from database import SessionLocal
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from models import Customer, Order, Product, Vendor, Supplier  # Supplier eklendi
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload  # joinedload eklendi
from routers.authentication import get_current_vendor
from fastapi.responses import RedirectResponse

load_dotenv()

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
vendor_dependency = Annotated[dict, Depends(get_current_vendor)]


async def generate_daily_summary(
        siparis_sayisi: int,
        bugunun_geliri: float,
        tamamlanan: int,
        kritik_stoklar: list,
        bu_ay_gelir: float,
        gecen_ay_gelir: float,
        bu_ay_siparis: int,
        gecen_ay_siparis: int,
        toplam_musteri: int,
) -> str:
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "GROQ_API_KEY bulunamadı."

        llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key)

        kritik_isimler = (
            ", ".join([p.name for p in kritik_stoklar[:3]])
            if kritik_stoklar else "Yok"
        )
        gelir_degisim = (
            round(((bu_ay_gelir - gecen_ay_gelir) / gecen_ay_gelir) * 100, 1)
            if gecen_ay_gelir > 0 else 0
        )

        prompt = (
            f"Sen bir KOBİ iş danışmanısın. Aşağıdaki verileri analiz et "
            f"ve işletme sahibine kısa, net, Türkçe öneriler sun. Maksimum 4 cümle.\n\n"
            f"Bugün: {siparis_sayisi} sipariş, {bugunun_geliri:.2f} TL gelir.\n"
            f"Tamamlanan: {tamamlanan}\n"
            f"Kritik Stoklar: {kritik_isimler}\n"
            f"Aylık Gelir: {bu_ay_gelir:.2f} TL (Değişim: %{gelir_degisim})\n"
            f"Toplam Müşteri: {toplam_musteri}"
        )

        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception:
        return "Yapay zeka analizi şu an hazırlanamadı."


@router.get("/")
async def dashboard(request: Request, vendor: vendor_dependency, db: db_dependency):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)

    vendor_id = int(vendor.get("id"))
    vendor_obj = db.query(Vendor).filter(Vendor.id == vendor_id).first()

    now = datetime.now(timezone.utc)
    bugun_start = datetime.combine(now.date(), datetime.min.time())
    bugun_end = datetime.combine(now.date(), datetime.max.time())
    bu_ay_start = datetime.combine(now.date().replace(day=1), datetime.min.time())
    gecen_ay_basi = (now.date().replace(day=1) - timedelta(days=1)).replace(day=1)
    gecen_ay_start = datetime.combine(gecen_ay_basi, datetime.min.time())

    # Bugünün Siparişleri
    bugun_sip = db.query(Order).filter(
        Order.vendor_id == vendor_id,
        Order.created_at >= bugun_start,
        Order.created_at <= bugun_end
    ).all()
    bugunun_siparis_sayisi = len(bugun_sip)
    bugunun_geliri = sum((o.price or 0) for o in bugun_sip)
    tamamlanan_siparis = sum(1 for o in bugun_sip if o.status == "Tamamlandı")

    # KRİTİK STOKLAR GÜNCELLEMESİ: Tedarikçi bilgilerini join ile çekiyoruz
    kritik_stoklar = db.query(Product).options(joinedload(Product.supplier)).filter(
        Product.vendor_id == vendor_id,
        Product.stock <= Product.min_stock_limit
    ).all()

    # Aylık Veriler
    bu_ay_sip = db.query(Order).filter(
        Order.vendor_id == vendor_id,
        Order.created_at >= bu_ay_start
    ).all()
    bu_ay_gelir = sum((o.price or 0) for o in bu_ay_sip)
    bu_ay_siparis_sayisi = len(bu_ay_sip)

    gecen_ay_sip = db.query(Order).filter(
        Order.vendor_id == vendor_id,
        Order.created_at >= gecen_ay_start,
        Order.created_at < bu_ay_start
    ).all()
    gecen_ay_gelir = sum((o.price or 0) for o in gecen_ay_sip)
    gecen_ay_siparis_sayisi = len(gecen_ay_sip)

    # Değişim Oranları
    gelir_degisim = (
        round(((bu_ay_gelir - gecen_ay_gelir) / gecen_ay_gelir) * 100, 1)
        if gecen_ay_gelir > 0 else 0
    )
    siparis_degisim = (
        round(((bu_ay_siparis_sayisi - gecen_ay_siparis_sayisi) / gecen_ay_siparis_sayisi) * 100, 1)
        if gecen_ay_siparis_sayisi > 0 else 0
    )
    toplam_musteri = db.query(func.count(Customer.id)).scalar() or 0

    # AI Analizi
    ai_ozet = await generate_daily_summary(
        bugunun_siparis_sayisi, bugunun_geliri, tamamlanan_siparis,
        kritik_stoklar, bu_ay_gelir, gecen_ay_gelir,
        bu_ay_siparis_sayisi, gecen_ay_siparis_sayisi, toplam_musteri
    )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "vendor": vendor_obj,
            "user": vendor_obj,
            "bugun": datetime.now().strftime("%d.%m.%Y"),
            "bugunun_siparis_sayisi": bugunun_siparis_sayisi,
            "bugunun_geliri": round(bugunun_geliri, 2),
            "tamamlanan_siparis": tamamlanan_siparis,
            "kritik_stoklar": kritik_stoklar,
            "bu_ay_gelir": round(bu_ay_gelir, 2),
            "gecen_ay_gelir": round(gecen_ay_gelir, 2),
            "gelir_degisim": gelir_degisim,
            "bu_ay_siparis_sayisi": bu_ay_siparis_sayisi,
            "gecen_ay_siparis_sayisi": gecen_ay_siparis_sayisi,
            "siparis_degisim": siparis_degisim,
            "toplam_musteri": toplam_musteri,
            "ai_ozet": ai_ozet,
        }
    )