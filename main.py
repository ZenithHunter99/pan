# main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uuid
import os

# import your Aadhaar verification functions
from pan.aadhaar_verifier import verify_aadhaar_card   # <-- your logic in aadhaar_verifier.py

app = FastAPI()

# ✅ Allow CORS so frontend can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or restrict to ["https://your-frontend.onrender.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/verify-aadhaar/")
async def verify_aadhaar(
    aadhaar_image: UploadFile = File(...),
    logo_image: UploadFile = File(...)
):
    try:
        # save temp files
        aadhaar_path = f"temp_{uuid.uuid4()}.png"
        logo_path = f"temp_logo_{uuid.uuid4()}.png"

        with open(aadhaar_path, "wb") as buffer:
            shutil.copyfileobj(aadhaar_image.file, buffer)

        with open(logo_path, "wb") as buffer:
            shutil.copyfileobj(logo_image.file, buffer)

        # run your verification logic
        result = verify_aadhaar_card(aadhaar_path, logo_path)

        # cleanup
        os.remove(aadhaar_path)
        os.remove(logo_path)

        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(content={"verified": False, "error": str(e)})
