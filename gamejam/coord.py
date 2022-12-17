class Coord2d():
    def __init__(self, x_val:float=0.0, y_val: float=0.0):
        self.x = x_val
        self.y = y_val
    

    def __add__(self, other):
        return Coord2d(self.x + other.x, self.y + other.y)


    def __sub__(self, other):
        return Coord2d(self.x - other.x, self.y - other.y)
        

    def __mul__(self, other):
        return Coord2d(self.x * other, self.y * other)
