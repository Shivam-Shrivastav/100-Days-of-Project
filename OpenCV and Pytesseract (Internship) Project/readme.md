Objective: In this OpenCV project we handled some given pdfs (Records of the accidents in LickingSheriff)
	   and our my task was to extrack some the useful text in a key value pair way and paste those useful data into a templates of pdfs.

Approach: 1. Since the pages of the pdfs were a Raster Images (the types of images that are produced when scanning or photographing an object),
	     so we cannot extract the text just using any pdfextracted library, therefore we use OpenCV to perform OCR to extract text from the image
	     form of the pages of the pdfs.
	  
     	  2. Since the pages of the pdfs are the scanned one's, the orientation of the pages are skewed with some angles [Refer lickingsheriff.pdf], for solving this problem
	     we use image coutours[Refer boxes_0.jpg] of OpenCV and make the skewed pages of the pdfs straight so that we can perform OCR [Refer lickingsheriff.pdf] and extract the texts.

	  3. Later with the help of PyPDF2 library we paste[Refer pasting.py] the extracted key value pair of the text in to the templates [Refer template pdfs] of pdfs and
	     we merged them all [Refer output pdfs]
	
	  