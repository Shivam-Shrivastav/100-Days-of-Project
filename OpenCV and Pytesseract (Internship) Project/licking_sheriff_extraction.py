from pdf2image import convert_from_path
import PIL
import pytesseract
import cv2
import numpy as np
import re
from PIL import Image, ImageEnhance
import pandas as pd
import math


def getSkewAngle(cvImage) -> float:
    # Prep image, copy, convert to gray scale, blur, and threshold
    newImage = cvImage.copy()
    gray = cv2.cvtColor(newImage, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    thresh = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Apply dilate to merge text into meaningful lines/paragraphs.
    # Use larger kernel on X axis to merge characters into single line, cancelling out any spaces.
    # But use smaller kernel on Y axis to separate between different blocks of text
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
    dilate = cv2.dilate(thresh, kernel, iterations=2)

    # Find all contours
    contours, hierarchy = cv2.findContours(
        dilate, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    for c in contours:
        rect = cv2.boundingRect(c)
        x, y, w, h = rect
        cv2.rectangle(newImage, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Find largest contour and surround in min area box
    largestContour = contours[0]
    minAreaRect = cv2.minAreaRect(largestContour)
    # Determine the angle. Convert it to the value that was originally used to obtain skewed image
    angle = minAreaRect[-1]
    if angle < -45:
        angle = 90 + angle
    if 87 <= angle <= 90:
        angle = 90 - angle
        angle = (-angle)

    return -1.0 * angle
# Rotate the image around its center


def rotateImage(cvImage, angle: float):
    newImage = cvImage.copy()
    (h, w) = newImage.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    newImage = cv2.warpAffine(
        newImage, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return newImage

# Deskew image


def deskew(cvImage):
    angle = getSkewAngle(cvImage)
    return rotateImage(cvImage, -1.0 * angle)


def cropwhitebg(img):
    img = np.array(img)

    # (1) Convert to gray, and threshold
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    th, threshed = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    # (2) Morph-op to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    morphed = cv2.morphologyEx(threshed, cv2.MORPH_CLOSE, kernel)

    # (3) Find the max-area contour
    cnts = cv2.findContours(morphed, cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)[-2]
    cnt = sorted(cnts, key=cv2.contourArea)[-1]

    # (4) Crop and save it
    x, y, w, h = cv2.boundingRect(cnt)
    dst = img[y:y+h, x:x+w]

    return Image.fromarray(dst)


def noise_removal(image):
    import numpy as np
    kernel = np.ones((2, 2), np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    kernel = np.ones((2, 2), np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    return (image)


def thin_font(image):
    import numpy as np
    image = cv2.bitwise_not(image)
    kernel = np.ones((2, 2), np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.bitwise_not(image)
    return (image)


def ocr(input_pdf, tesseract_exe_path):
    images = convert_from_path(input_pdf)
    def remove_unwanted(text): return re.sub('[~;|",)“(._-]', '', text)
    def remove_unwanted1(text): return re.sub('[~‘;|",:)“(._]', '', text)
    def remove_lower(text): return re.sub('[a-z]', '', text)
    lastpage = False
    def remove_letters(text): return re.sub('[A-Za-z]', '', text)
    fixed = []
    for i in range(0, len(images)):
        con = ImageEnhance.Brightness(images[i])
        images[i] = con.enhance(1.5)
        fixed.append('fixedimage{}'.format(i))
        new = cv2.cvtColor(np.array(images[i]), cv2.COLOR_RGB2BGR)
        fixed[i] = deskew(new)
        fixed[i] = noise_removal(fixed[i])
        fixed[i] = thin_font(fixed[i])
        fixed[i] = Image.fromarray(fixed[i])
        fixed[i] = cropwhitebg(fixed[i])
        con = ImageEnhance.Contrast(fixed[i])
        fixed[i] = con.enhance(5)
        fixed[i] = cv2.resize(np.array(fixed[i]), (1591, 2095))
        gray = cv2.cvtColor(fixed[i], cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        # Remove horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        remove_horizontal = cv2.morphologyEx(
            thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
        cnts = cv2.findContours(
            remove_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            cv2.drawContours(fixed[i], [c], -1, (255, 255, 255), 6)
        # Remove vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        remove_vertical = cv2.morphologyEx(
            thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
        cnts = cv2.findContours(
            remove_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            cv2.drawContours(fixed[i], [c], -1, (255, 255, 255), 5)
        fixed[i] = Image.fromarray(fixed[i])
        bri = ImageEnhance.Brightness(fixed[i])
        fixed[i] = bri.enhance(1.5)
        # display(fixed[i])

    pdf = []
    count = -1
    for i in range(0, len(images)):
        tcr = fixed[i].crop((179, 4, 575, 46))
        tcr = np.array(tcr)
        tcr = cv2.resize(tcr, None, fx=1.5, fy=1.5,
                         interpolation=cv2.INTER_CUBIC)
        tcr = cv2.cvtColor(tcr, cv2.COLOR_BGR2GRAY)
        tcr = cv2.medianBlur(tcr, 3)
        tcr = Image.fromarray(tcr)
        # display(tcr)
        pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
        text = pytesseract.image_to_string(tcr, lang='eng')
        text = text.strip()
        text = text.upper()
        # print(text)
        if re.findall(r'\bT', text) or re.findall('FRAFFIC', text) or re.findall('CRASH REPORT', text) or re.findall('CRASH', text) or re.findall('RASH', text) or re.findall('PORT', text):
            count = count+1
            pdf.append([])
        pdf[count].append(fixed[i])
        narr = fixed[i].crop((185, 4, 728, 65))
        narr = np.array(narr)
        narr = cv2.resize(narr, None, fx=5, fy=5,
                          interpolation=cv2.INTER_CUBIC)
        narr = cv2.cvtColor(narr, cv2.COLOR_BGR2GRAY)
        narr = cv2.medianBlur(narr, 3)
        pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
        nartext = pytesseract.image_to_string(narr, lang='eng')
        nartext = nartext.strip()
        if re.findall('Narrative', nartext) or re.findall('Continuation', nartext):
            pdf[count].remove(fixed[i])

    import pandas as pd
    dfs = []
    totpg_list = []
    for p in range(0, len(pdf)):
        dfs.append([])
        for i in range(0, len(pdf[p])):
            dfs[p].append('df{}'.format(i))
            dfs[p][i] = pd.DataFrame()
    nan_value = float("NaN")
    for p in range(0, len(pdf)):
        for i in range(0, len(pdf[p])):
            total_pages = len(pdf[p])
            if i == 0:
                print(total_pages,"TOTAL")
                clmns = ['LOCAL REPORT NUMBER', 'REPORTING AGENCY NAME',
                         'NCIC', 'COUNTY', 'NUMBER OF UNITS', 'CRASH DATE/TIME']
                p1 = [1069, 435, 908,   22,   1265,  1054]
                p2 = [48,   122, 120,   195,  115,   198]
                p3 = [1535, 900, 1045,  90,   1328,  1318]
                p4 = [93,   171, 163,   237,  163,   246]
                for h in range(0, len(clmns)):
                    key = ''
                    value = ''
                    img = pdf[p][i].crop((p1[h], p2[h], p3[h], p4[h]))
                    con = ImageEnhance.Brightness(img)
                    img = con.enhance(1.8)
                    display(img)
                    img = np.array(img)
                    img = cv2.resize(img, None, fx=2, fy=2.3,
                                     interpolation=cv2.INTER_CUBIC)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                    text = pytesseract.image_to_string(
                        img, lang='eng', config='--psm 6')
                    text = text.strip()
                    clean_text = text.split('\n')
                    clean_text = list(filter(''.__ne__, clean_text))
                    key = clmns[h]
                    if len(clean_text) != 0:
                        value = clean_text[0]
                    if key == 'LOCAL REPORT NUMBER':
                        value = value.replace("Q", "")
                        value = value.replace(" ", "")
                        value = value.replace("O", "0")
                        value = value.replace("o", "0")
                        value = value.replace(":", "")
                    if key == 'REPORTING AGENCY NAME':
                        value = value.replace(",",".")
                        value = value.replace("$","S")
                    if key == 'COUNTY':
                        value = value.replace(" ", "")
                        value = remove_unwanted1(value)
                        if len(value)>2:
                            value = value.replace(value[1:-1],"")
                    if key == 'NUMBER OF UNITS':
                        value = value.replace("Q", "")
                        value = value.replace("O", "0")
                        value = value.replace("o", "0")
                        value = value.replace("9", "0")
                        value = value.replace(" ", "")
                        value = value.replace(',', '')
                    if key == 'NCIC':
                        value = value.replace(" ","")
                        value = value.replace(":","")
                        value = remove_unwanted1(value)
                    if re.findall(r'CRASH', key):
                        value = value.replace(" ", "")
                        value = value.replace("£", "")
                        value = value.replace(",", "")
                        value = value.replace(".", "")
                        value = value.replace("#", "")
                        value = value.replace("|", "")
                        value = value.replace(";", "")
                        value = value.replace("=", "")
                        value = value.replace(":", "")
                        value = value.replace("/", "")
                        value = value.replace("L", "1")


                        mm = value[0:2]
                        dd = value[2:4]
                        yy = value[4:8]
                        hr = value[8:10]
                        mn = value[10:12]
                        se = "00"
                        s = "/"
                        seq = (mm, dd, yy)
                        date = s.join(seq)
                        s = ":"
                        seq = (hr, mn, se)
                        time = s.join(seq)
                        s = " "
                        seq = (date, time)
                        value = s.join(seq)
                        key = 'CRASH DATE/TIME'
                    if key != 'REPORTING AGENCY NAME':
                        value = remove_unwanted(value)
                    print(key, ": ", value)

                    dfs[p][i][key] = pd.Series(value)

                # Unit In Error
                clmns = ['uniterror']
                p1 = [1385]
                p2 = [121]
                p3 = [1458]
                p4 = [163]
                for h in range(0, len(clmns)):
                    key = ''
                    value = ''
                    img = pdf[p][i].crop((p1[h], p2[h], p3[h], p4[h]))
                    con = ImageEnhance.Brightness(img)
                    img = con.enhance(1.8)
                    display(img)
                    img = np.array(img)
                    img = cv2.resize(img, None, fx=0.7, fy=1,
                                     interpolation=cv2.INTER_NEAREST)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                    text = pytesseract.image_to_string(
                        img, config='--psm 6 --psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
                    text = text.strip()
                    clean_text = text.split('\n')
                    clean_text = list(filter(''.__ne__, clean_text))
                    key = 'UNIT IN ERROR'
                    value = clean_text[0]
                    value = remove_unwanted(value)
                    value = value.replace("o", "0")
                    value = value.replace("O", "0")
                    print(key, ": ", value)
                    dfs[p][i][key] = pd.Series(value)

                # Crash Severity
                clmns = ['crashsecVal']
                p1 = [1337]
                p2 = [186]
                p3 = [1375]
                p4 = [234]
                for h in range(0, len(clmns)):
                    key = ''
                    value = ''
                    img1 = pdf[p][i].crop((p1[h], p2[h], p3[h], p4[h]))
                    bri = ImageEnhance.Brightness(img1)
                    img1 = bri.enhance(1.8)
                    display(img1)
                    img1 = np.array(img1)
                    img1 = cv2.resize(img1, None, fx=1.7,
                                      fy=1.7, interpolation=cv2.INTER_CUBIC)
                    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                    pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                    text1 = pytesseract.image_to_string(
                        img1, config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')
                    key = 'CRASH SEVERITY'
                    value = text1.split('\n')[0]
                    value = remove_unwanted(value)
                    print(key, ": ", value)
                    dfs[p][i][key] = pd.Series(value)

                    no_ut = dfs[p][0].loc[0, 'NUMBER OF UNITS']
                    no_ut = no_ut.replace("0", "")
                    dfs[p][0].loc[0, 'NUMBER OF UNITS'] = dfs[p][0].loc[0, 'NUMBER OF UNITS'][-1]

                # Narrative
                clmns = ['narrative']
                p1 = [18]
                p2 = [1312]
                p3 = [786]
                p4 = [1867]
                for h in range(0, len(clmns)):
                    key = ''
                    value = ''
                    img = pdf[p][i].crop((p1[h], p2[h], p3[h], p4[h]))
                    display(img)
                    img = np.array(img)
                    img = cv2.resize(img, None, fx=5, fy=5,
                                     interpolation=cv2.INTER_CUBIC)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                    text = pytesseract.image_to_string(
                        img, lang='eng', config='--psm 6')
                    text = text.strip()
                    clean_text = text.split('\n')
                    clean_text = list(filter(''.__ne__, clean_text))
                    key = 'NARRATIVE'
                    value = clean_text[:]
                    value = " ".join(value)
                    value = value.upper()
                    value = value.replace("_", "")
                    value = value.replace("|", "")
                    value = value.replace("__", "")
                    value = value.replace("—-", "")

                    print(key, ": ", value)
                    dfs[p][i][key] = pd.Series(value)

            if int(no_ut) >= 1 and i == 1:
                for u in range(1, (int(no_ut)+1)):
                    print(int(no_ut), 'no_ut')
                    print(u, 'u')
                    h1 = ['VEHICLE YEAR', 'VEHICLE MAKE', 'VEHICLE MODEL', 'INSURANCE COMPANY', 'INSURANCE POLICY #',
                          'OWNER PHONE NUMBER - INC. AREA CODE', 'OWNER NAME: LAST, FIRST, MIDDLE', 'OWNER ADDRESS: CITY, STATE, ZIP']
                    p1 = [762, 886,  887,  146, 466,  705, 109, 27]
                    p2 = [267, 273,  327,  323, 325,  95,  97, 156]
                    p3 = [877, 1050, 1050, 449, 748, 1041, 684, 864]
                    p4 = [301, 300,  358,  356, 364, 126,  128, 183]

                    for j in range(0, len(h1)):
                        key = ''
                        value = ''
                        img = pdf[p][u].crop((p1[j], p2[j], p3[j], p4[j]))
                        display(img)
                        bri = ImageEnhance.Brightness(img)
                        img = bri.enhance(1.3)
                        img = np.array(img)
                        img = cv2.resize(img, None, fx=1.5,
                                         fy=1.5, interpolation=cv2.INTER_CUBIC)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                        text = pytesseract.image_to_string(
                            img, lang='eng', config='--psm 6')
                        text = text.strip()
                        clean_text = text.split('\n')
                        clean_text = list(filter(''.__ne__, clean_text))
                        clean_text = list(filter(' '.__ne__, clean_text))
                        key = h1[j]
                        if len(clean_text) != 0:
                            value = clean_text[0]
                            value = value.upper()
                        if key == 'OWNER NAME: LAST, FIRST, MIDDLE':
                            value = value
                            value = ''.join([v for v in value if not v.isdigit()]) 
                        if key == 'OWNER ADDRESS: CITY, STATE, ZIP':
                            value = value
                        else:
                            value = remove_unwanted1(value)
                        if re.findall(r'PHONE', key):
                            value = remove_letters(value)
                            value = value.replace(" ", "")
                            value = value.replace(" ", "")
                            value = value.replace("-", "")
                            value = value.replace("—", "")
                            value = value.replace("«", "")
                            if len(value) < 10:
                                print(len(value))
                                value = value.replace(value, "")
                        if key =="VEHICLE YEAR":
                            value = value.replace(" ","")
                            value = remove_letters(value)
                            value = remove_unwanted1(value)
                            value = value.replace("|","")
                            value = value.replace("/","")
                            value = value.replace("\\","")
                            if len(value)<4:
                                value = ""
                        print(key, ": ", value)
                        dfs[p][u][key] = pd.Series(value)

                    # Unit
                    clmns = ['unitVal']
                    p1 = [34, ]
                    p2 = [96, ]
                    p3 = [94, ]
                    p4 = [122, ]
                    for h in range(0, len(clmns)):
                        key = ''
                        value = ''
                        img1 = pdf[p][u].crop((p1[h], p2[h], p3[h], p4[h]))
                        img1 = np.array(img1)
                        img1 = cv2.resize(img1, None, fx=1.5,
                                          fy=1.5, interpolation=cv2.INTER_CUBIC)
                        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                        img1 = cv2.medianBlur(img1, 1)
                        pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                        text1 = pytesseract.image_to_string(
                            img1, lang='eng', config='--psm 10 --psm 6 --psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
                        key = 'UNIT #'
                        text1 = text1.strip()
                        value = text1.split('\n')[0]
                        if re.findall(r'UN', key):
                            key = 'UNIT #'
                            if len(value) > 0:
                                value = value[-1]
                            value = value.replace("Q", "0")
                            value = value.replace("q", "0")
                            value = value.replace("11", "1")
                        dfs[p][u][key] = pd.Series(value)

                    # Occupants
                    clmns = ['occupantsVal']
                    p1 = [342]
                    p2 = [462]
                    p3 = [408]
                    p4 = [496]
                    for h in range(0, len(clmns)):
                        key = ''
                        value = ''
                        img1 = pdf[p][u].crop((p1[h], p2[h], p3[h], p4[h]))
                        display(img1)
                        bri = ImageEnhance.Brightness(img1)
                        img1 = bri.enhance(1.4)
                        img1 = np.array(img1)
                        img1 = cv2.resize(img1, None, fx=1.2,
                                          fy=1.2, interpolation=cv2.INTER_CUBIC)
                        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                        pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                        text1 = pytesseract.image_to_string(img1, lang='eng',
                                                            config='--psm 6 --psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
                        key = '# OCCUPANTS'
                        text1 = text1.strip()
                        value = text1.split('\n')[0]
                        value = remove_unwanted(value)
                        if len(value)>=1:
                            value = int(value)
                            value = str(value)
                        print(key, ": ", value)
                        dfs[p][u][key] = pd.Series(value)

                    # Unit Type
                    clmns = ['unittypeVal']
                    p1 = [42]
                    p2 = [537]
                    p3 = [96]
                    p4 = [573]
                    for h in range(0, len(clmns)):
                        key = ''
                        value = ''
                        img1 = pdf[p][u].crop((p1[h], p2[h], p3[h], p4[h]))
                        bri = ImageEnhance.Brightness(img1)
                        img1 = bri.enhance(2.5)
                        display(img1)
                        img1 = np.array(img1)
                        img1 = cv2.resize(img1, None, fx=1.4,
                                          fy=1.5, interpolation=cv2.INTER_NEAREST)
                        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                        pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                        text1 = pytesseract.image_to_string(img1, lang='eng',
                                                            config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')
                        key = 'UNIT TYPE'
                        text1 = text1.strip()
                        value = text1.split('\n')[0]
                        value = remove_unwanted(value)
                        if len(value) > 0:
                            value = int(value)
                        print(key, ": ", value)
                        dfs[p][u][key] = pd.Series(value)

                    # Damage Scale
                    clmns = ['damagescaleVal']
                    p1 = [1070]
                    p2 = [137]
                    p3 = [1135]
                    p4 = [171]
                    for h in range(0, len(clmns)):
                        key = ''
                        value = ''
                        img1 = pdf[p][u].crop((p1[h], p2[h], p3[h], p4[h]))
                        display(img1)
                        img1 = np.array(img1)
                        img1 = cv2.resize(img1, None, fx=0.7,
                                          fy=0.9, interpolation=cv2.INTER_CUBIC)
                        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                        pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                        text1 = pytesseract.image_to_string(img1, lang='eng',
                                                            config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')
                        key = 'DAMAGE SCALE'
                        value = text1.split('\n')[0]
                        value = remove_unwanted(value)
                        print(key, ": ", value)
                        dfs[p][u][key] = pd.Series(value)

                    if 'LOCAL REPORT NUMBER' not in dfs[p][u].columns:
                        dfs[p][u].insert(
                            0, 'LOCAL REPORT NUMBER', dfs[p][0].iloc[0, 0])
                    else:
                        dfs[p][u]['LOCAL REPORT NUMBER'] = dfs[p][0].iloc[0, 0]
                    dfs[p][u]['UNIT #'] = dfs[p][u].apply(lambda row: '' if (row['UNIT #'] == '' or math.isnan(
                        float(row['UNIT #']))) else str(int(row['UNIT #'])), axis=1)

                dfs[p][u]['UNIT #'] = dfs[p][u].apply(lambda row: '' if (row['UNIT #'] == '' or math.isnan(
                    float(row['UNIT #']))) else str(int(row['UNIT #'])), axis=1)

            if int(no_ut) % 3 == 0:
                mot = int(int(no_ut)/3)
            else:
                mot = int(int(no_ut)/3)+1

            if mot > 0 and (int(no_ut)+1) <= i < (int(no_ut)+mot+1):
                for m in range(i, i+1):
                    dict0 = {}
                    dict2 = {}
                    dict3 = {}
                    h1 = ['UNIT #', 'NAME: LAST, FIRST, MIDDLE', 'DATE OF BIRTH', 'AGE', 'GENDER', 'INJURIES',
                          'SEATING POSITION', 'CONTACT PHONE - INCLUDE AREA CODE', 'ADDRESS: CITY STATE ZIP']
                    h = [h1, h1, h1]
                    a = 397
                    h1p1 = [35,  121, 1044,  1410, 1517, 49, 1205,  1053, 27]
                    h1p2 = [107, 116, 112,   113,  110,  257, 256,  180, 188]
                    h1p3 = [103,  976, 1394,  1492, 1556, 75, 1303, 1570, 969]
                    h1p4 = [152, 154, 143,   144,  141,  286, 290,  218, 224]

                    h2p1 = [35,  121, 1044,  1410, 1517, 49, 1205,  1053, 27]
                    h2p2 = [107+a, 116+a, 112+a,   113+a,
                            110+a,  257+a, 256+a,  180+a, 188+a]
                    h2p3 = [103,  976, 1394,  1492, 1556, 75, 1303, 1570, 969]
                    h2p4 = [152+a, 154+a, 143+a,   144+a,
                            141+a,  286+a, 290+a,  218+a, 224+a]

                    h3p1 = [35,  121, 1044,  1410, 1517, 49, 1205,  1053, 27]
                    h3p2 = [107+(2*a), 116+(2*a), 112+(2*a),   113+(2*a),
                            110+(2*a),  257+(2*a), 256+(2*a),  180+(2*a), 188+(2*a)]
                    h3p3 = [103,  976, 1394,  1492, 1556, 75, 1303, 1570, 969]
                    h3p4 = [152+(2*a), 154+(2*a), 143+(2*a),   144+(2*a),
                            141+(2*a),  286+(2*a), 290+(2*a),  218+(2*a), 224+(2*a)]

                    p1 = [h1p1, h2p1, h3p1]
                    p2 = [h1p2, h2p2, h3p2]
                    p3 = [h1p3, h2p3, h3p3]
                    p4 = [h1p4, h2p4, h3p4]
                    for num in range(len(h)):
                        dict1 = [dict0, dict2, dict3]
                        for j in range(0, (len(h[num]))):
                            key = ''
                            value = ''
                            img = pdf[p][m].crop(
                                (p1[num][j], p2[num][j], p3[num][j], p4[num][j]))
                            con = ImageEnhance.Brightness(img)
                            img = con.enhance(1.1)

                            display(img)
                            img = np.array(img)
                            img = cv2.resize(
                                img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_NEAREST)
                            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            img = cv2.medianBlur(img, 1)
                            pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                            text = pytesseract.image_to_string(
                                img, lang='eng', config='--psm 6')
                            text = text.strip()
                            clean_text = text.split('\n')
                            clean_text = list(filter(''.__ne__, clean_text))
                            if len(clean_text) != 0:
                                value = clean_text[0]
                                value = value.upper()
                            key = h1[j]
                            if key == 'GENDER':
                                img = Image.fromarray(img)
                                con = ImageEnhance.Contrast(img)
                                img = con.enhance(1.3)
                                img = np.array(img)
                                img = cv2.resize(
                                    img, None, fx=0.8, fy=0.8, interpolation=cv2.INTER_NEAREST)
                                text = pytesseract.image_to_string(
                                    img, lang='eng', config='--psm 10 --psm 6 --psm 7')
                                text = text.strip()
                                clean_text = text.split('\n')
                                clean_text = list(
                                    filter(''.__ne__, clean_text))
                                if len(clean_text) != 0 and clean_text[0] != 'M' and clean_text[0] != 'F':
                                    clean_text.pop()
                                if len(clean_text) != 0:
                                    value = clean_text[0][0]
                            if key == 'AGE':
                                img = Image.fromarray(img)
                                bri = ImageEnhance.Contrast(img)
                                img = bri.enhance(1.3)
                                img = np.array(img)
                                img = noise_removal(img)
                                img = cv2.resize(img, None, fx=0.9, fy=0.9)
                                text = pytesseract.image_to_string(
                                    img, config='--psm 6 --psm 10 --oem 3 -c tessedit_char_whitelist=,|\/;:0123456789')
                                text = text.strip()
                                img = Image.fromarray(img)
                                display(img)
                                clean_text = text.split('\n')
                                clean_text = list(
                                    filter(''.__ne__, clean_text))
                                if len(clean_text) != 0:
                                    value = clean_text[0]
                                    if len(value)>2:
                                        value = value.replace(value[1:-1],"")
                            if key == 'SEATING POSITION':
                                img = Image.fromarray(img)
                                con = ImageEnhance.Brightness(img)
                                img = con.enhance(2)
                                con = ImageEnhance.Contrast(img)
                                img = con.enhance(2)
                                img = np.array(img)
                                img = cv2.resize(img, None, fx=0.5, fy=0.9, interpolation=cv2.INTER_NEAREST)
                                text = pytesseract.image_to_string(
                                    img, config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
                                text = text.strip()
                                img = Image.fromarray(img)
                                display(img)
                                clean_text = text.split('\n')
                                clean_text = list(
                                    filter(''.__ne__, clean_text))
                                if len(clean_text) != 0:
                                    value = clean_text[0]
                                    if value[0] =="6":
                                        value = list(value)
                                        value[0] = "0"
                                        value = "".join(value)
                                    if value[0] !="1":
                                            value = list(value)
                                            value[0] = "0"
                                            value = "".join(value)
                                    if len(value)>2:
                                        value = value.replace(value[1:-1],"")
                                        value = remove_unwanted1(value)
                                value = value.replace("o", "0")
                                value = value.replace("O", "0")
                                value = value.replace("I", "1")
                                value = value.replace("i", "1")
                                value = value.replace(",", "")
                                value = value.replace("/", "")
                                value = value.replace("'", "")
                                value = value.replace(";", "")
                                value = value.replace("‘", "")
                                value = value.replace("\\", "")
                                value = value.replace(" ", "")
                                value = value.replace("|", "")


                                value = remove_letters(value)
                                if len(value) > 0:
                                    value = int(value)
                                    value = str(value)
                                    print(value)
                            if key == 'INJURIES':
                                img = Image.fromarray(img)
                                img = np.array(img)
                                img = cv2.resize(img, None, fx=0.9, fy=0.9, interpolation=cv2.INTER_NEAREST)
                                text = pytesseract.image_to_string(
                                    img, config='--psm 10 --psm 6 --psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
                                text = text.strip()
                                clean_text = text.split('\n')
                                clean_text = list(
                                    filter(''.__ne__, clean_text))
                                img = Image.fromarray(img)
                                display(img)
                                if len(clean_text) != 0:
                                    value = clean_text[0]
                                    if value == "S":
                                        value = "5"
                            if key == 'UNIT #':
                                value = value.replace("o", "0")
                                value = value.replace("O", "0")
                                value = value.replace("Q", "0")
                                value = value.replace("G", "0")
                                value = value.replace("g", "0")
                                value = value.replace("q", "0")
                                value = value.replace("11", "1")
                                value = value.replace("I", "1")
                                value = value.replace("i", "1")
                                value = value.replace("L", "1")
                                value = value.replace("l", "1")
                                value = value.replace("—", "")
                                value = value.replace("E", "")
                            if key == 'DATE OF BIRTH':
                                img = Image.fromarray(img)
                                bri = ImageEnhance.Contrast(img)
                                img = bri.enhance(5)
                                img = np.array(img)
                                img = cv2.resize(img, None, fx=1, fy=1.3, interpolation=cv2.INTER_NEAREST)
                                text = pytesseract.image_to_string(
                                    img, config='--psm 7 --oem 3 -c tessedit_char_whitelist=/0123456789')
                                text = text.strip()
                                print(text,'dob')
                                img = Image.fromarray(img)
                                display(img)
                                clean_text = text.split('\n')
                                clean_text = list(
                                    filter(''.__ne__, clean_text))
                                if len(clean_text) != 0:
                                    value = clean_text[0]
                                    print(value,'dob')
                                    if len(value)==10:
                                        if value[0] =="9":
                                            value = list(value)
                                            value[0] = "0"
                                            value = "".join(value)
                                        if value[0] =="2":
                                            value = list(value)
                                            value[0] = "1"
                                            value = "".join(value)
                                value = value.replace(" ", "")
                                value = value.replace("°", "")
                                value = value.replace("{", "")
                                value = value.replace("<", "")
                                value = value.replace("o", "0")
                                value = value.replace("O", "0")
                                value = value.replace("//", "/")
                                value = remove_letters(value)
                                print(value,'dob')
                                if len(value) == 9:
                                    value = "0"+value
                                if len(value) < 10:
                                    value = ""
                            if key == 'NAME: LAST, FIRST, MIDDLE' or key == 'ADDRESS: CITY STATE ZIP':
                                value = value
                            else:
                                value = remove_unwanted1(value)
                                value = value.replace(" ", "")
                            if key == 'NAME: LAST, FIRST, MIDDLE':
                                value = ''.join([v for v in value if not v.isdigit()])
                            if key == 'CONTACT PHONE - INCLUDE AREA CODE':
                                value = remove_letters(value)
                                value = remove_unwanted1(value)
                                value = value.replace("™", "")
                                value = value.replace("É", "")
                                value = value.replace("—", "")
                                value = value.replace("«", "")
                                value = value.replace("'", "")

                                if len(value) < 10:
                                    print(len(value))
                                    value = value.replace(value, "")
                            if key == 'INJURIES':
                                if value == "S":
                                    value = "5"
                            print(key, ": ", value)
                            dict1[num][key] = value
                        dfs[p][m] = dfs[p][m].append(
                            dict1[num], ignore_index=True)
                        print(m, 'MOTORIST')
                        if dfs[p][m]['GENDER'][num] == "" and dfs[p][m]['DATE OF BIRTH'][num] == "" and dfs[p][m]['INJURIES'][num] == "":
                            dfs[p][m]['AGE'][num] = ""
                            dfs[p][m]['SEATING POSITION'][num] = ""
                        if dfs[p][m]['INJURIES'][num] == "" and dfs[p][m]['SEATING POSITION'][num] == "1":
                            dfs[p][m]['SEATING POSITION'][num] = ""
                        if dfs[p][m]['SEATING POSITION'][num] == "0":
                            dfs[p][m]['SEATING POSITION'][num] = "1"
                        if 'LOCAL REPORT NUMBER' not in dfs[p][m].columns:
                            dfs[p][m].insert(
                                0, 'LOCAL REPORT NUMBER', dfs[p][0].iloc[0, 0])
                        else:
                            dfs[p][m]['LOCAL REPORT NUMBER'] = dfs[p][0].iloc[0, 0]
                        dfs[p][m]['UNIT #'] = dfs[p][m].apply(lambda row: '' if (row['UNIT #'] == '' or math.isnan(
                            float(row['UNIT #']))) else str(int(row['UNIT #'])), axis=1)

            if (int(no_ut)+mot+1) <= i < total_pages:
                for o in range(i, i+1):
                    dict5 = {}
                    dict6 = {}
                    dict7 = {}
                    dict8 = {}

                    h1 = ['UNIT #', 'NAME: LAST, FIRST, MIDDLE', 'DATE OF BIRTH', 'AGE', 'GENDER', 'INJURIES',
                          'SEATING POSITION', 'CONTACT PHONE - INCLUDE AREA CODE', 'ADDRESS: STREET, CITY, STATE, ZIP']
                    h = [h1, h1, h1, h1]
                    b = 228
                    h1p1 = [42,  128,   1051, 1417, 1520,  50, 1210, 1052, 28]
                    h1p2 = [103, 105,   106,   113, 111,   256, 262, 171, 185]
                    h1p3 = [83,  933,   1395, 1483,
                            1553,  75, 1292, 1577, 1015]
                    h1p4 = [139, 144,   140,   146, 140,   286, 290, 215, 222]

                    h2p1 = [42,  128,   1051, 1417, 1520,  50, 1210, 1052, 28]
                    h2p2 = [103+b, 105+b,   106+b,   113+b,
                            111+b,   256+b, 262+b, 171+b, 185+b]
                    h2p3 = [83,  933,   1395, 1483,
                            1553,  75, 1292, 1577, 1015]
                    h2p4 = [139+b, 144+b,   140+b,   146+b,
                            140+b,   286+b, 290+b, 215+b, 222+b]

                    h3p1 = [42,  128,   1051, 1417, 1520,  50, 1210, 1052, 28]
                    h3p2 = [103+(2*b), 105+(2*b),   106+(2*b),   113+(2*b),
                            111+(2*b),   256+(2*b), 262+(2*b), 171+(2*b), 185+(2*b)]
                    h3p3 = [83,  933,   1395, 1483,
                            1553,  75, 1292, 1577, 1015]
                    h3p4 = [139+(2*b), 144+(2*b),   140+(2*b),   146+(2*b),
                            140+(2*b),   286+(2*b), 290+(2*b), 215+(2*b), 222+(2*b)]

                    h4p1 = [42,  128,   1051, 1417, 1520,  50, 1210, 1052, 28]
                    h4p2 = [103+(3*b), 105+(3*b),   106+(3*b),   113+(3*b),
                            111+(3*b),   256+(3*b), 262+(3*b), 171+(3*b), 185+(3*b)]
                    h4p3 = [83,  933,   1395, 1483,
                            1553,  75, 1292, 1577, 1015]
                    h4p4 = [139+(3*b), 144+(3*b),   140+(3*b),   146+(3*b),
                            140+(3*b),   286+(3*b), 290+(3*b), 215+(3*b), 222+(3*b)]

                    p1 = [h1p1, h2p1, h3p1, h4p1]
                    p2 = [h1p2, h2p2, h3p2, h4p2]
                    p3 = [h1p3, h2p3, h3p3, h4p3]
                    p4 = [h1p4, h2p4, h3p4, h4p4]

                    for num in range(len(h)):
                        dict4 = [dict5, dict6, dict7, dict8]
                        for j in range(0, (len(h[num]))):
                            key = ''
                            value = ''
                            img = pdf[p][o].crop(
                                (p1[num][j], p2[num][j], p3[num][j], p4[num][j]))
                            con = ImageEnhance.Brightness(img)
                            img = con.enhance(1.1)
                            display(img)
                            img = np.array(img)
                            img = cv2.resize(
                                img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_NEAREST)
                            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            img = cv2.medianBlur(img, 1)
                            pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
                            text = pytesseract.image_to_string(
                                img, lang='eng', config='--psm 6')
                            text = text.strip()
                            clean_text = text.split('\n')
                            clean_text = list(filter(''.__ne__, clean_text))
                            if len(clean_text) != 0:
                                value = clean_text[0]
                                value = value.upper()
                            key = h1[j]
                            if key == 'GENDER':
                                img = Image.fromarray(img)
                                con = ImageEnhance.Contrast(img)
                                img = con.enhance(1.3)
                                img = np.array(img)
                                img = cv2.resize(
                                    img, None, fx=0.8, fy=0.8, interpolation=cv2.INTER_NEAREST)
                                text = pytesseract.image_to_string(
                                    img, lang='eng', config='--psm 10 --psm 6 --psm 7')
                                text = text.strip()
                                clean_text = text.split('\n')
                                clean_text = list(
                                    filter(''.__ne__, clean_text))
                                if len(clean_text) != 0 and clean_text[0] != 'M' and clean_text[0] != 'F':
                                    clean_text.pop()
                                if len(clean_text) != 0:
                                    value = clean_text[0][0]
                            if key == 'AGE':
                                img = Image.fromarray(img)
                                bri = ImageEnhance.Contrast(img)
                                img = bri.enhance(1.4)
                                img = np.array(img)
                                img = noise_removal(img)
                                img = cv2.resize(img, None, fx=0.9, fy=0.9)
                                text = pytesseract.image_to_string(
                                    img, config='--psm 6 --psm 10 --oem 3 -c tessedit_char_whitelist=,|\/;:0123456789')
                                text = text.strip()
                                img = Image.fromarray(img)
                                display(img)
                                clean_text = text.split('\n')
                                clean_text = list(
                                    filter(''.__ne__, clean_text))
                                if len(clean_text) != 0:
                                    value = clean_text[0]
                                    if len(value)>2:
                                        value = value.replace(value[1:-1],"")
                            if key == 'SEATING POSITION':
                                img = Image.fromarray(img)
                                con = ImageEnhance.Brightness(img)
                                img = con.enhance(2)
                                con = ImageEnhance.Contrast(img)
                                img = con.enhance(2)
                                img = np.array(img)
                                img = cv2.resize(img, None, fx=0.5, fy=0.9)
                                text = pytesseract.image_to_string(
                                    img, config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
                                text = text.strip()
                                img = Image.fromarray(img)
                                display(img)
                                clean_text = text.split('\n')
                                clean_text = list(
                                    filter(''.__ne__, clean_text))
                                if len(clean_text) != 0:
                                    value = clean_text[0]
                                    if len(value)==10:
                                        if value[0] =="6":
                                            value = list(value)
                                            value[0] = "0"
                                            value = "".join(value)
                                        if value[0] !="1":
                                            value = list(value)
                                            value[0] = "0"
                                            value = "".join(value)
                                        if len(value)>2:
                                            value = value.replace(value[1:-1],"")
                                            value = remove_unwanted1(value)
                                value = value.replace("o", "0")
                                value = value.replace("O", "0")
                                value = value.replace("I", "1")
                                value = value.replace("i", "1")
                                value = value.replace(" ", "")
                                value = value.replace(",", "")
                                value = value.replace("/", "")
                                value = value.replace(".", "")
                                value = value.replace(";", "")
                                value = value.replace("‘", "")
                                value = value.replace("\\", "")
                                value = value.replace("|", "")
                                value = remove_letters(value)
                                if len(value) > 0:
                                    value = int(value)
                                    value = str(value)
                                    print(value)
                            if key == 'INJURIES':
                                img = Image.fromarray(img)
                                img = np.array(img)
                                img = cv2.resize(
                                    img, None, fx=0.9, fy=0.9, interpolation=cv2.INTER_NEAREST)
                                text = pytesseract.image_to_string(
                                    img, config='--psm 10 --psm 6 --psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
                                text = text.strip()
                                clean_text = text.split('\n')
                                clean_text = list(
                                    filter(''.__ne__, clean_text))
                                img = Image.fromarray(img)
                                display(img)
                                if len(clean_text) != 0:
                                    value = clean_text[0]
                                    if value == "S":
                                        value = "5"
                            if key == 'DATE OF BIRTH':
                                img = Image.fromarray(img)
                                bri = ImageEnhance.Contrast(img)
                                img = bri.enhance(5)
                                img = np.array(img)
                                img = cv2.resize(img, None, fx=1, fy=1.3, interpolation=cv2.INTER_NEAREST)
                                text = pytesseract.image_to_string(
                                    img, config='--psm 7 --oem 3 -c tessedit_char_whitelist=/0123456789')
                                text = text.strip()
                                print(text,'dob')
                                img = Image.fromarray(img)
                                display(img)
                                clean_text = text.split('\n')
                                clean_text = list(
                                    filter(''.__ne__, clean_text))
                                if len(clean_text) != 0:
                                    value = clean_text[0]
                                    if value[0] =="9":
                                        value = list(value)
                                        value[0] = "0"
                                        value = "".join(value)
                                    if value[0] =="2":
                                        value = list(value)
                                        value[0] = "1"
                                        value = "".join(value)
                                print(value,'dob')
                                value = value.replace(" ", "")
                                value = value.replace("°", "")
                                value = value.replace("{", "")
                                value = value.replace("<", "")
                                value = value.replace("o", "0")
                                value = value.replace("O", "0")
                                value = value.replace("//", "/")
                                value = remove_letters(value)
                                print(value,'dob')
                                if len(value) == 9:
                                    value = "0"+value
                                if len(value) < 10:
                                    value = ""
                            if key == 'UNIT #':
                                value = value.replace("o", "0")
                                value = value.replace("O", "0")
                                value = value.replace("Q", "0")
                                value = value.replace("q", "0")
                                value = value.replace("G", "0")
                                value = value.replace("g", "0")
                                value = value.replace("11", "1")
                                value = value.replace("I", "1")
                                value = value.replace("L", "1")
                                value = value.replace("l", "1")
                                value = value.replace("i", "1")
                                value = value.replace("E", "")
                                value = value.replace("—", "")
                            if key == 'NAME: LAST, FIRST, MIDDLE' or key == 'ADDRESS: STREET, CITY, STATE, ZIP':
                                value = value
                            else:
                                value = remove_unwanted1(value)
                                value = value.replace(" ","")
                            if key == 'NAME: LAST, FIRST, MIDDLE':
                                value = ''.join([v for v in value if not v.isdigit()])

                            if key == 'CONTACT PHONE - INCLUDE AREA CODE':
                                value = remove_letters(value)
                                value = remove_unwanted1(value)
                                value = value.replace(" ", "")
                                value = value.replace("-", "")
                                value = value.replace("—", "")
                                value = value.replace("«", "")
                                value = value.replace("É", "")
                                value = value.replace("'", "")
                                if len(value) < 10:
                                    print(len(value))
                                    value = value.replace(value, "")
                            if key == 'INJURIES':
                                if value == "S":
                                    value = "5"
                            print(key, ": ", value)
                            dict4[num][key] = value
                        dfs[p][o] = dfs[p][o].append(
                            dict4[num], ignore_index=True)
                        print(o, 'ORCUP')
                        if dfs[p][o]['GENDER'][num] == "" and dfs[p][o]['DATE OF BIRTH'][num] == "" and dfs[p][o]['INJURIES'][num] == "" :
                            dfs[p][o]['AGE'][num] = ""
                            dfs[p][o]['SEATING POSITION'][num] = ""
                        if dfs[p][o]['INJURIES'][num] == "" and dfs[p][o]['SEATING POSITION'][num] == "1":
                            dfs[p][o]['SEATING POSITION'][num] = ""
                        if dfs[p][o]['SEATING POSITION'][num] == "0":
                            dfs[p][o]['SEATING POSITION'][num] = "1"
                        if 'LOCAL REPORT NUMBER' not in dfs[p][o].columns:
                            dfs[p][o].insert(
                                0, 'LOCAL REPORT NUMBER', dfs[p][0].iloc[0, 0])
                        else:
                            dfs[p][o]['LOCAL REPORT NUMBER'] = dfs[p][0].iloc[0, 0]

                    dfs[p][o]['UNIT #'] = dfs[p][o].apply(lambda row: '' if (row['UNIT #'] == '' or math.isnan(
                        float(row['UNIT #']))) else str(int(row['UNIT #'])), axis=1)
        for k in range(0, total_pages):
            dfs[p][k].replace("", nan_value, inplace=True)
            dfs[p][k].replace("//", nan_value, inplace=True)
            dfs[p][k] = dfs[p][k].dropna(axis=0, how='all')
            dfs[p][k].replace(nan_value, "", inplace=True)

        for ut in range(1, int(no_ut)+1):
            dfs[p][ut]['VEHICLE MODEL'] = dfs[p][ut].apply(
                lambda row: row['VEHICLE MODEL'][:10], axis=1)
            dfs[p][ut]['VEHICLE MAKE'] = dfs[p][ut].apply(
                lambda row: row['VEHICLE MAKE'][:10], axis=1)

        for ut in range(1, int(no_ut)+1):
            for mt in range(int(no_ut)+1, int(no_ut)+1+mot):
                for m in range(0, len(dfs[p][mt])):
                    if dfs[p][ut]['OWNER NAME: LAST, FIRST, MIDDLE'][0] == '' and dfs[p][ut]['UNIT #'][0] == dfs[p][mt]['UNIT #'][m]:
                        dfs[p][ut]['OWNER NAME: LAST, FIRST, MIDDLE'] = dfs[p][mt]['NAME: LAST, FIRST, MIDDLE'][m]
                    if dfs[p][ut]['OWNER ADDRESS: CITY, STATE, ZIP'][0] == '' and dfs[p][ut]['UNIT #'][0] == dfs[p][mt]['UNIT #'][m]:
                        dfs[p][ut]['OWNER ADDRESS: CITY, STATE, ZIP'] = dfs[p][mt]['ADDRESS: CITY STATE ZIP'][m]
                    if dfs[p][ut]['OWNER PHONE NUMBER - INC. AREA CODE'][0] == '' and dfs[p][ut]['UNIT #'][0] == dfs[p][mt]['UNIT #'][m]:
                        dfs[p][ut]['OWNER PHONE NUMBER - INC. AREA CODE'] = dfs[p][mt]['CONTACT PHONE - INCLUDE AREA CODE'][m]

        dfs[p][0]['UNIT IN ERROR'] = dfs[p][0].apply(
            lambda row: int(row['UNIT IN ERROR']), axis=1)
        totpg_list.append(total_pages)

    return dfs, pdf, totpg_list
