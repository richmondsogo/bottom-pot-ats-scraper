import random


penalty_location = ('left', 'right', 'center')
penalty_angle = ('top','bottom','middle')

a = random.choices(penalty_angle)
b = random.choices(penalty_location)

print(a + b)
