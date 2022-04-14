def paster(ls, dictionary, df, path, i, total_pages, bwl, alignment):
    import io
    from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from PIL import ImageFont

    font = ImageFont.truetype('Helvetica.ttf',7)

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter, bottomup = 0)

    for num in range(0,len(df)):
        for val in range(0, len(ls[num])):
            if alignment[num][val] == 'C':   
                width = 0
                for c in str(df.iloc[num][ls[num][val]]):
                    width += font.getsize(c)[0] 
                text = can.beginText((dictionary[num][ls[num][val]][0] + ((bwl[num][val]-width)/2)), dictionary[num][ls[num][val]][1])
            else:
                text = can.beginText(dictionary[num][ls[num][val]][0], dictionary[num][ls[num][val]][1])
            text.setFont('Helvetica', 7)
            text.textLines(str(df.iloc[num][ls[num][val]]))
            can.drawText(text)
    if i==0 and df.columns[8]== 'NARRATIVE':
        x = 23
        y = 492.5
        a = 8
        xyz = df['NARRATIVE'][0]
        length = 0
        narrativeList = []
        t = []
        g = 0
        smallest = []
        s =0
        for l, r in enumerate(xyz.split(" ")):
            length+= len(r)+1
            if length <= 60:
                narrativeList.append(r.upper())
                narrative= " ".join(narrativeList)
                if (len(xyz.split(" "))-g)<=s and (len(xyz.split(" "))-l) == 1:
                    t.append(narrative)         
            if length > 60:
                g = l
                smallest.append((len(xyz.split(" "))-g))
                s = smallest[len(smallest)-1]
                length = 0 + len(r)
                t.append(narrative)
                narrativeList = []
                narrativeList.append(r.upper())
                if (len(xyz.split(" "))-(g+1))==0:
                    narrative= " ".join(narrativeList)
                    t.append(narrative)
        for k in range(0, len(t)):
            text = can.beginText(x, y+(k*a))
            text.setFont('Helvetica', 7)
            text.textLines(t[k])
            can.drawText(text)

    text1 = can.beginText(561.0, 788.4)
    text1.setFont('Times-Roman',8)
    text1.textLines(str(i+1))
    can.drawText(text1)
    text2 = can.beginText(580.3, 788.4)
    text2.setFont('Times-Roman',8)
    text2.textLines(str(total_pages))
    can.drawText(text2)
    can.save()
    packet.seek(0)
    new_pdf = PdfFileReader(packet)
    existing_pdf = PdfFileReader(open(path, "rb"))
    output = PdfFileWriter()
    page = existing_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0))
    output.addPage(page)
    outputStream = open('output_'+str(i)+'.pdf', "wb")
    output.write(outputStream)
    outputStream.close()
    return 'output_'+str(i)+'.pdf'

def merger(pdfs, lrn, jurisdiction):
    from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
    import os
    merger = PdfFileMerger()
    for pdf in pdfs:
        merger.append(pdf)
    merger.write(jurisdiction+'_OCR{}.pdf'.format(lrn))
    merger.close()
    for pdf in pdfs:
        os.remove(pdf)

def main(main_page_template_path, unit_template_path, motorist_template_path, occupant_template_path, pdfs, total_pages, dfs, jurisdiction): 
    for p in range(0, total_pages):
        if p == 0:
            pdfs[p]= main_page_template_path
        no_ut = dfs[0].loc[0,'NUMBER OF UNITS']
        no_ut =no_ut.replace("0 ","")
        int(no_ut)
        if int(no_ut)>=1 and p==1:
            for p in range(1,(int(no_ut)+1)):
                pdfs[p] = unit_template_path
                
        if int(no_ut)%3==0:
            mot = int(int(no_ut)/3)
        else:
            mot = int(int(no_ut)/3)+1
            
        if mot >0 and (int(no_ut)+1)<=p<(int(no_ut)+mot+1):
            for p in range(p,p+1):
                pdfs[p] = motorist_template_path

        if p>=(int(no_ut)+mot+1):
            for p in range(p, total_pages):
                pdfs[p] = occupant_template_path
            
    for i in range(0,total_pages):
        if i == 0:
            boxwidth = [[80, 150, 60, 15, 61, 20, 8, 15 ]]
            alignment = [['C','L','C','L','L','C','L','C',]]
            clmns = [['LOCAL REPORT NUMBER', 'REPORTING AGENCY NAME', 'NCIC', 'COUNTY', 'CRASH DATE/TIME', 'NUMBER OF UNITS', 'CRASH SEVERITY', 'UNIT IN ERROR',]]
            dictcl = [{'LOCAL REPORT NUMBER':[455, 35.3], 'REPORTING AGENCY NAME':[169.9, 60.5], 'NCIC':[330, 60.5], 'COUNTY':[30.2, 88.6], 'CRASH DATE/TIME':[419.8, 88.6], 'NUMBER OF UNITS':[472, 60.5], 'CRASH SEVERITY':[505.4, 88.6], 'UNIT IN ERROR':[520, 60.5], 'NARRATIVE':[23, 492.5]}]
            path = main_page_template_path
            pdfs[i] = paster(clmns, dictcl, dfs[i], path, i, total_pages, boxwidth, alignment)
            from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
                
        no_ut = dfs[0].loc[0,'NUMBER OF UNITS']
        no_ut =no_ut.replace("0 ","")
        int(no_ut)
        if int(no_ut)>=1 and i==1:
            for j in range(1,(int(no_ut)+1)):
                boxwidth = [[80, 20, 160, 200, 35, 45, 45, 80, 90, 15, 20, 75, 8]]
                alignment = [['C','R','L','L','C','L','L','L','L','C','L','C','R']]
                clmns = [['LOCAL REPORT NUMBER', 'UNIT #', 'OWNER NAME: LAST, FIRST, MIDDLE', 'OWNER ADDRESS: CITY, STATE, ZIP', 'VEHICLE YEAR', 'VEHICLE MAKE', 'VEHICLE MODEL', 'INSURANCE COMPANY', 'INSURANCE POLICY #', '# OCCUPANTS', 'UNIT TYPE', 'OWNER PHONE NUMBER - INC. AREA CODE', 'DAMAGE SCALE']]
                dictcl = [{'LOCAL REPORT NUMBER':[455, 40.3], 'UNIT #':[30.2, 63.4], 'OWNER NAME: LAST, FIRST, MIDDLE':[50.4, 63.4], 'OWNER ADDRESS: CITY, STATE, ZIP':[23, 83.5], 'VEHICLE YEAR':[290, 127.4], 'VEHICLE MAKE':[349.9, 127.4], 'VEHICLE MODEL':[349.9, 147.6], 'INSURANCE COMPANY':[65.5, 147.6], 'INSURANCE POLICY #':[185, 147.6], '# OCCUPANTS':[140, 195.1], 'UNIT TYPE':[35.3, 220.3], 'OWNER PHONE NUMBER - INC. AREA CODE':[295, 63.4], 'DAMAGE SCALE':[415.4, 79.9]}]
                path = unit_template_path
                pdfs[j]= paster(clmns, dictcl, dfs[j], path, j, total_pages, boxwidth, alignment)
        
    
        if mot >0 and (int(no_ut)+1)<=i<(int(no_ut)+mot+1):
            for j in range(i,i+1):

                offset = 147
                boxwidth0 = [80, 200, 15, 50, 10, 10, 200, 12, 15, 75]
                boxwidth1 = [200, 15, 50, 10, 10, 200, 12, 15, 75]
                boxwidth = [boxwidth0, boxwidth1, boxwidth1] 

                alignment0 = ['C','L','R','R','R','L','L','C','L','C']
                alignment1 = ['L','R','R','R','L','L','C','L','C']
                alignment = [alignment0, alignment1, alignment1]

                clmns0 = ['LOCAL REPORT NUMBER', 'ADDRESS: CITY STATE ZIP', 'AGE', 'DATE OF BIRTH', 'GENDER', 'INJURIES', 'NAME: LAST, FIRST, MIDDLE', 'SEATING POSITION', 'UNIT #', 'CONTACT PHONE - INCLUDE AREA CODE']            
                clmns1 = ['ADDRESS: CITY STATE ZIP', 'AGE', 'DATE OF BIRTH', 'GENDER', 'INJURIES', 'NAME: LAST, FIRST, MIDDLE', 'SEATING POSITION', 'UNIT #', 'CONTACT PHONE - INCLUDE AREA CODE']            
                clmns = [clmns0, clmns1, clmns1]
                dictcl0 = {'LOCAL REPORT NUMBER':[450, 32.4], 'ADDRESS: CITY STATE ZIP':[30.2, 85], 'AGE':[540, 60.5], 'DATE OF BIRTH':[450, 60.5], 'GENDER':[575.3, 60.5], 'INJURIES':[35.3, 115.2], 'NAME: LAST, FIRST, MIDDLE':[60.5, 58.3], 'SEATING POSITION':[466, 115.2], 'UNIT #':[35.3, 60.5], 'CONTACT PHONE - INCLUDE AREA CODE':[400, 84]}
                dictcl1 = {'ADDRESS: CITY STATE ZIP':[30.2, 230.4], 'AGE':[540, 205.2], 'DATE OF BIRTH':[450, 205.2], 'GENDER':[575.3, 205.2], 'INJURIES':[35.3, 259.9], 'NAME: LAST, FIRST, MIDDLE':[60.5, 204], 'SEATING POSITION':[466, 259.9], 'UNIT #':[35.3, 205.2], 'CONTACT PHONE - INCLUDE AREA CODE':[400, 229.4]}
                dictcl2 = {'ADDRESS: CITY STATE ZIP':[30.2, 83+(2*offset)], 'AGE':[540, 58+(2*offset)], 'DATE OF BIRTH':[450, 58+(2*offset)], 'GENDER':[575.3, 58+(2*offset)], 'INJURIES':[35.3, 115.2+(2*offset)], 'NAME: LAST, FIRST, MIDDLE':[60.5, 57+(2*offset)], 'SEATING POSITION':[466, 115.2+(2*offset)], 'UNIT #':[35.3, 58+(2*offset)], 'CONTACT PHONE - INCLUDE AREA CODE':[400, 82+(2*(offset))]}
                dictcl = [dictcl0,dictcl1,dictcl2]
                    
                path = motorist_template_path
                pdfs[j] = paster(clmns, dictcl, dfs[i], path, j, total_pages, boxwidth, alignment)

        if  i>=(int(no_ut)+mot+1):
            for j in range(i, total_pages):

                offset = 83
                boxwidth0 = [80, 15, 50, 10, 10, 200, 12, 200, 15, 75]
                boxwidth1 = [15, 50, 10, 10, 200, 12, 200, 15, 75]
                boxwidth = [boxwidth0, boxwidth1, boxwidth1, boxwidth1]

                alignment0 = ['C','L','L','L','L','L','C','L','L','C']
                alignment1 = ['L','L','L','L','L','C','L','L','C']
                alignment = [alignment0, alignment1, alignment1, alignment1]

                clmns0 = ['LOCAL REPORT NUMBER', 'AGE', 'DATE OF BIRTH', 'GENDER', 'INJURIES', 'NAME: LAST, FIRST, MIDDLE', 'SEATING POSITION', 'ADDRESS: STREET, CITY, STATE, ZIP', 'UNIT #', 'CONTACT PHONE - INCLUDE AREA CODE']
                clmns1 = ['AGE', 'DATE OF BIRTH', 'GENDER', 'INJURIES', 'NAME: LAST, FIRST, MIDDLE', 'SEATING POSITION', 'ADDRESS: STREET, CITY, STATE, ZIP', 'UNIT #', 'CONTACT PHONE - INCLUDE AREA CODE']
                clmns = [clmns0, clmns1 , clmns1, clmns1]
                dictcl0 = {'LOCAL REPORT NUMBER':[450, 32.4],'AGE':[540, 60.5],  'DATE OF BIRTH':[450, 60.5], 'GENDER':[575.3, 60.5], 'INJURIES':[35.3, 115.2], 'NAME: LAST, FIRST, MIDDLE':[60.5, 58.3], 'SEATING POSITION':[466, 115.2], 'ADDRESS: STREET, CITY, STATE, ZIP':[31, 85], 'UNIT #':[35.3, 60.5], 'CONTACT PHONE - INCLUDE AREA CODE':[400, 84.2]}
                dictcl1 = {'AGE':[540, 143.3],  'DATE OF BIRTH':[450, 143.3], 'GENDER':[575.3, 143.3], 'INJURIES':[35.3, 198], 'NAME: LAST, FIRST, MIDDLE':[60.5, 141.1], 'SEATING POSITION':[466, 198], 'ADDRESS: STREET, CITY, STATE, ZIP':[31, 168.5], 'UNIT #':[35.3, 143.3], 'CONTACT PHONE - INCLUDE AREA CODE':[400, 167.7]}
                dictcl2 = {'AGE':[540, 228.2], 'DATE OF BIRTH':[450, 228.2], 'GENDER':[575.3, 228.2], 'INJURIES':[35.3, 281.5], 'NAME: LAST, FIRST, MIDDLE':[60.5, 223.9], 'SEATING POSITION':[466, 281.5], 'ADDRESS: STREET, CITY, STATE, ZIP':[31, 251.3], 'UNIT #':[35.3, 228.2], 'CONTACT PHONE - INCLUDE AREA CODE':[400, 82+(2*offset)]}
                dictcl3 = {'AGE':[540, 58+(3*offset)], 'DATE OF BIRTH':[450, 58+(3*offset)], 'GENDER':[575.3, 58+(3*offset)], 'INJURIES':[35.3, 111+(3*offset)], 'NAME: LAST, FIRST, MIDDLE':[60.5, 57+(3*offset)], 'SEATING POSITION':[466, 112+(3*offset)], 'ADDRESS: STREET, CITY, STATE, ZIP':[31, 83+(3*offset)], 'UNIT #':[35.3, 58+(3*offset)], 'CONTACT PHONE - INCLUDE AREA CODE':[400, 82+(3*offset)]}
                dictcl = [dictcl0,dictcl1, dictcl2, dictcl3]
                
                path = occupant_template_path
                pdfs[j] = paster(clmns, dictcl, dfs[i], path, j, total_pages, boxwidth, alignment)
    
    lrn = dfs[0].iloc[0,0]
    lrn = lrn.replace(" ", "")
    merger(pdfs, lrn, jurisdiction)

if __name__ == "__main__":
    main(main_page_template_path, unit_template_path, motorist_template_path, occupant_template_path, pdfs, total_pages, dfs, jurisdiction)
