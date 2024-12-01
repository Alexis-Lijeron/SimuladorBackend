import stripe
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

stripe.api_key = "api_key"

@router.post("/create-payment-intent")
async def create_payment_intent(amount: int):
    try:
        if amount <= 0:
            raise HTTPException(status_code=422, detail="Amount must be greater than zero")

        intent = stripe.PaymentIntent.create(
            amount=amount,  # Monto en centavos
            currency="USD",  # Asegúrate de usar la moneda correcta
            payment_method_types=["card"],
        )
        return JSONResponse(content={"clientSecret": intent["client_secret"]})
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=422, detail=f"Stripe error: {e.user_message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

