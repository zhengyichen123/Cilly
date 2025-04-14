

import turtle

def fern(len):
    if len > 5 :
        turtle.forward(len)
        turtle.right(10)
        fern(len - 10)
        turtle.left(40)
        fern(len - 10)
        turtle.right(30)
        turtle.backward(len)


turtle.pencolor("green")
turtle.left(90)
turtle.penup()
turtle.backward(200)
turtle.pendown()
fern(100)

