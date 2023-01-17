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


    def to_list(self) -> list:
        return [self.x, self.y]


    def from_list(self, coord_list: list):
        if len(coord_list) > 1:
            self.x = coord_list[0]
            self.y = coord_list[1]


    def from_string(self, string: str):
        scomps = string.replace(" ", "").split(",")
        self.from_list([float(s) for s in scomps])
