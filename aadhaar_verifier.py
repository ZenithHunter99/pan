# ------------------ Imports ------------------
import cv2
import re
from pyzbar.pyzbar import decode
import xml.etree.ElementTree as ET
import numpy as np
import pytesseract

# ------------------ QR Verification ------------------
def parse_aadhaar_xml(data: str):
    """Parse Aadhaar QR XML data if present"""
    try:
        root = ET.fromstring(data)
        details = {
            "uid": root.attrib.get("uid"),
            "name": root.attrib.get("name"),
            "gender": root.attrib.get("gender"),
            "dob": root.attrib.get("dob"),
            "gname": root.attrib.get("gname"),
            "house": root.attrib.get("house"),
            "street": root.attrib.get("street"),
            "lm": root.attrib.get("lm"),
            "vtc": root.attrib.get("vtc"),
            "po": root.attrib.get("po"),
            "dist": root.attrib.get("dist"),
            "state": root.attrib.get("state"),
            "pc": root.attrib.get("pc")
        }
        return {"status": True, "data": details}
    except Exception:
        return {"status": False, "raw_data": data}

def verify_aadhaar_qr(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        return {"status": False, "reason": "Image not found"}

    h, w, _ = img.shape
    qr_region = img[0:h, 0:w]

    # Try pyzbar
    decoded = decode(qr_region)
    if decoded:
        for obj in decoded:
            qr_data = obj.data.decode("utf-8", errors="ignore")
            parsed = parse_aadhaar_xml(qr_data)
            if parsed["status"]:
                return {"status": True, "method": "pyzbar", "aadhaar_number": parsed["data"]["uid"]}
            match = re.search(r"\d{12}", qr_data)
            if match:
                return {"status": True, "method": "pyzbar", "aadhaar_number": match.group()}

    # Fallback: OpenCV QRCodeDetector
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(qr_region)
    if data:
        parsed = parse_aadhaar_xml(data)
        if parsed["status"]:
            return {"status": True, "method": "opencv", "aadhaar_number": parsed["data"]["uid"]}
        match = re.search(r"\d{12}", data)
        if match:
            return {"status": True, "method": "opencv", "aadhaar_number": match.group()}

    return {"status": False, "reason": "QR not detected or invalid"}

def detect_aadhaar_logo_feature(image_path, logo_path, match_thresh=15):
    img = cv2.imread(image_path, 0)
    h, w = img.shape
    rg = img[0:h//2, 0:w]
    logo = cv2.imread(logo_path, 0)

    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(logo, None)
    kp2, des2 = orb.detectAndCompute(rg, None)

    if des1 is None or des2 is None:
        return False

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    good_matches = [m for m in matches if m.distance < 50]
    return len(good_matches) >= match_thresh

# ------------------ Text Extraction / Aadhaar Number ------------------
def extract_aadhaar_number_from_text(image_path):
    img = cv2.imread(image_path)
    text = pytesseract.image_to_string(img)
    text_cleaned = text.replace('\n', ' ').replace('|', ' ').replace('_', ' ')
    pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    match = re.search(pattern, text_cleaned)
    if match:
        return match.group()
    return None

# ------------------ Integrated Aadhaar Verification Pipeline ------------------
def verify_aadhaar_card(image_path, logo_path):
    # Step 1: Try QR verification
    qr_result = verify_aadhaar_qr(image_path)
    if qr_result.get("status"):
        return {"verified": True, "method": "QR", "aadhaar_number": qr_result.get("aadhaar_number")}

    # Step 2: Logo detection + OCR fallback
    logo_ok = detect_aadhaar_logo_feature(image_path, logo_path)
    if not logo_ok:
        return {"verified": False, "reason": "Logo not detected"}

    aadhaar_number = extract_aadhaar_number_from_text(image_path)
    if aadhaar_number:
        return {"verified": True, "method": "Logo+Text", "aadhaar_number": aadhaar_number}
    
    return {"verified": True, "reason": "Aadhaar number not detected ⚠️ Reupload"}

# ------------------ Example Usage ------------------
if __name__ == "__main__":
    image_path = "test.png" 
    logo_path = "template.jpg"

    result = verify_aadhaar_card(image_path, logo_path)
    print(result)