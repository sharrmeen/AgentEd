import cv2
import pytesseract

def extract_text_preprocessed(image_path):
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found or cannot be read: {image_path}")


    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Denoise
    denoised = cv2.medianBlur(thresh, 3)

    # OCR
    text = pytesseract.image_to_string(denoised, lang="eng")
    return text

if __name__ == "__main__":
    path = "/Users/sharmeenkhan/AgentEd/backend/app/services/image.png"
    result = extract_text_preprocessed(path)
    print("Extracted Text:\n", result)
