import os
import httpx
from fastapi import APIRouter, Request, Response
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from database import SessionLocal
from models import Order, Customer, Product

load_dotenv()

router = APIRouter(prefix="/webhook", tags=["WhatsApp"])

WHATSAPP_TOKEN   = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID  = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN     = os.getenv("VERIFY_TOKEN")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")

@router.get("/")
async def verify_webhook(request: Request):
    params = request.query_params
    mode         = params.get("hub.mode") or params.get("hub_mode")
    verify_token = params.get("hub.verify_token") or params.get("hub_verify_token")
    challenge    = params.get("hub.challenge") or params.get("hub_challenge")

    if mode == "subscribe" and verify_token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)

@router.post("/")
async def receive_message(request: Request):
    body = await request.json()

    try:
        entry    = body["entry"][0]
        changes  = entry["changes"][0]["value"]
        if "messages" not in changes:
            return {"status": "ok"}

        message  = changes["messages"][0]
        from_num = message["from"]
        text     = message["text"]["body"]

    except (KeyError, IndexError):
        return {"status": "ok"}
    reply = await generate_reply(text, from_num)
    await send_whatsapp_message(from_num, reply)

    return {"status": "ok"}

async def generate_reply(user_message: str, phone_number: str) -> str:
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(
            Customer.phone_number == phone_number
        ).first()
        if customer:
            orders = db.query(Order).filter(
                Order.customer_id == customer.id
            ).order_by(Order.created_at.desc()).limit(5).all()

            order_info = "\n".join([
                f"- Sipariş #{o.id}: {o.status}, "
                f"Ürün ID {o.product_id}, "
                f"{o.quantity} adet, "
                f"{o.price:.2f} TL"
                for o in orders
            ]) if orders else "Sipariş bulunamadı."

            musteri_bilgi = (
                f"Müşteri: {customer.first_name} {customer.last_name}\n"
                f"Son 5 sipariş:\n{order_info}"
            )
        else:
            musteri_bilgi = "Bu numara sistemde kayıtlı değil."
        products = db.query(Product).limit(10).all()
        stok_bilgi = "\n".join([
            f"- {p.name}: {p.stock} {p.unit}, {p.price:.2f} TL"
            for p in products
        ])

    finally:
        db.close()
    prompt = f"""Sen bir KOBİ'nin WhatsApp müşteri destek asistanısın.
Kısa, samimi ve yardımcı cevaplar ver. Maksimum 3 cümle. Türkçe yaz.

Müşteri bilgisi:
{musteri_bilgi}

Mevcut ürünler ve stok:
{stok_bilgi}

Müşteri mesajı: {user_message}

Eğer sipariş durumu soruyorsa sipariş bilgilerini ver.
Eğer ürün veya stok soruyorsa stok bilgilerini ver.
Eğer başka bir konu ise kibarca yönlendir."""

    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception:
        return "Şu an bir sorun yaşıyoruz, lütfen daha sonra tekrar deneyin."

async def send_whatsapp_message(to: str, message: str):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload, headers=headers)