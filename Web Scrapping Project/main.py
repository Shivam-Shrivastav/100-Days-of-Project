# Step 0: Install and Import all the requirements
import requests
from bs4 import BeautifulSoup, element
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
url = 'https://insights.blackcoffer.com/how-is-login-logout-time-tracking-for-employees-in-office-done-by-ai/'
r = requests.get(url,  headers={"User-Agent": "XY"})
print(r)

# # Step 1: Get the HTML
# r = requests.get(url)
# print(r)
htmlContent = r.content

# Step 2: Parse the HTML
soup = BeautifulSoup(htmlContent, 'html.parser')

# Step 3: HTML Tree Traversal
# # Commonly ised types of objects:



# # 4. Comment


# # print(title)
# # print(type(title)) # 1. Tag
# # print(type(title.string)) # 2. Navigable String
# # print('\n')
# # print(type(soup)) # 3. BeautifulSoup
# title = soup.title

from pprint import pprint as pp
# # Get all the paragraphs from the page
paras = soup.find_all('p')
hd = soup.find_all('a')

k = str(paras)
k = k.replace('[', '')
k = k.replace(']', '')
k = k.replace('<p>', '')
k = k.replace('</p>', '')
# print(k)
# pp(hd)



# # Get all the anchor tags from the page
# anchors = soup.find_all('a')
# print(anchors)

# # print(soup.find('p')) #Get First Element
print(soup.find('td-post-content')['class']) #Get Classes of any element in HTML mage

# # find all the elements with class lead
# # print(soup.find_all("p", class_= "mt-2"))

# # Get the text from the tags/soup
# print(soup.find('p').get_text())
# print(soup.get_text())

# #Get the all links on the page


# # all_links = set()
# # for link in anchors:
# #     if(link.get('href')!= '#'):
# #         linktext = "https://codewithharry.com/" + link.get('href')
# #         all_links.add(linktext)
# #         # print(linktext)

# # markup = "<p><!--this is a comment --></p>"
# # soup2 = BeautifulSoup(markup)
# # # print(type(soup2.p.string)) #Comment in BS4
# # exit()

  







