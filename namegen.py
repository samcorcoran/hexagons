import random

def generateName(length=10):
    name = ""
    vowel = ['a', 'e', 'i', 'o', 'u', 'y']
    consonant = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z']
    v = False
    for i in range(random.randint(5,12)):
        if v:
            name += random.choice(vowel)
        else:
            name += random.choice(consonant)
        v = not v
    name = name.capitalize()
    return name
