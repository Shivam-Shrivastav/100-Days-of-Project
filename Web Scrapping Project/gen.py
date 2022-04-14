fruit = ['Apple', 'Mango', 'Banana', 'Grape', 'Guava']

def get_fruit(fruit):
    for i, f in enumerate(fruit):
        yield i, f

num = get_fruit(fruit)

for x in num:
    print(x[1])