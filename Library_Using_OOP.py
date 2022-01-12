class Library:

    def __init__(self, list_of_books, library_name):
        self.listofbooks = list_of_books
        self.libraryname = library_name
        self.lendDict = {}

    def displayBooks(self):
        print(f"\n{self.libraryname}'s library have following books:")
        for books in self.listofbooks:
            print(books)

    def lendBooks(self,book, user):
        if book not in self.lendDict.keys() and book in self.listofbooks:
            self.lendDict.update({book:user})
            self.listofbooks.remove(book)
            print("The book is available you can take the book")
        elif book not in self.listofbooks:
            print(f"Sorry!! the book {book} has not been added to the library yet")
        elif book in self.lendDict.keys():
            print(f"Sorry!! the book has been lend to {self.lendDict[book]} you can take the book later")

    def addBooks(self,book):
        self.listofbooks.append(book)
        if book in self.listofbooks:
            print(f"The {book} has been added to {self.libraryname}'s Library")

    def returnBooks(self,book):
        self.lendDict.pop(book)
        self.listofbooks.append(book)

def main():
    shivam = Library(["Python", "The One Thing", "DEC", "Alchemist", "Atomic Habbits", "Think and Grow Rich", "Theory of Everything"], "Shivam Shrivastava")

    while(True):
        print(f"\nWelcome to {shivam.libraryname}'s Library!!\nChoose Following Options:\n1. To Display Books\n2. To Lend Books\n3. To Add Books\n4. To Return Books\n5. To Quit\n")
        inp1 = input()
        if inp1 not in ["1", "2", "3", "4", "5"]:
            inp1 = inp1
        else:
            inp1 = int(inp1)
        if inp1 == 1:
            shivam.displayBooks()
        elif inp1 ==2:
            book = input("Enter the Book you want to lend: \n")
            user = input("Enter your name:\n")
            shivam.lendBooks(book, user)
        elif inp1 == 3:
            book = input("Enter the name of the book you want to add:\n")
            shivam.addBooks(book)
        elif inp1 == 4:
            book = input("Enter the name of the book you want to return:\n")
            shivam.returnBooks(book)
        elif inp1 == 5:
            break
        else:
            print("Enter valid option please!\n")
            continue
    

if __name__ == "__main__":
    main()
    
