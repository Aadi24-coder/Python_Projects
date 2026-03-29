import random
c=0
num=random.randint(1,100)
while True :
    a=int(input("enter your guess "))
    c=c+1
    if (c==7):
        print(f"GAME OVER ! THE NUMBER WAS {num}")
    if(a==num):
        print("your guess is correct : ")
        break
    elif(a<num):
        print("too low!")
    else:
        print("too high!")
if(c<5):
    print(f"WOW ONLY {c} ATTEMPTS NICE ! ")



