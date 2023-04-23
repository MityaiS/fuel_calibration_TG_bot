import pytesseract
import cv2
import logging


logger = logging.getLogger(__name__)


async def get_str_from_image(name, threshold):

    image = cv2.imread(name)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY_INV)[1]

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 1))
    detected_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    cnts = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(image, [c], -1, (255, 255, 255), 2)

    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 10))
    detected_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    cnts = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(image, [c], -1, (255, 255, 255), 2)

    data = pytesseract.image_to_data(image, config="--psm 6 -c tessedit_char_whitelist=0123456789",
                                     output_type=pytesseract.Output.DICT)

    string = ""
    prev_num = 0
    for i in range(len(data["conf"])):
        logger.debug(f"{data['conf'][i]}, {data['text'][i]}")
        if data["conf"][i] > 90 and not int(data["text"][i]) < prev_num:
            string += data["text"][i]
            prev_num = int(data["text"][i])
            string += "\n"
        elif data["conf"][i] > -1:
            string += "u/r"
            string += "\n"

    cv2.imshow("image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return string


async def get_fuel_data(text):
    text = text.replace(",", ".")
    num_str = ""

    for c in text:
        if c.isdigit() or c == ".":
            num_str += c
        else:
            num_str += " "
    num_str = num_str.strip(". ")
    num_str = num_str.split()[-1]
    num_str = num_str.strip(".")

    return float(num_str)
