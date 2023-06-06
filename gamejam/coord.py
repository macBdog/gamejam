import math
from abc import ABC, abstractmethod

class Coord(ABC):
    """TODO: Change this to a numpy array with property accessors and compare speed:
    @property
    def x(self):
        return self[0]


    @property
    def y(self):
        return self[1]


    def __eq__(self, other):
        return np.array_equal(self, other)


    def __ne__(self, other):
        return not np.array_equal(self, other)


    def __iter__(self):
        for x in np.nditer(self):
            yield x.item()


    def __abs__(self):
        return np.linalg.norm(self)


    def dist(self,other):
        return np.linalg.norm(self-other)


    def dot(self, other):
        return np.dot(self, other)

    """
    @abstractmethod
    def __repr__(self):
        pass


    @abstractmethod
    def __add__(self, other):
        pass


    @abstractmethod
    def __sub__(self, other):
        pass


    @abstractmethod
    def __mul__(self, other):
        pass


    @abstractmethod
    def to_list(self) -> list:
        pass

    @abstractmethod
    def from_list(self, coord_list: list):
        pass


    @abstractmethod
    def from_string(self, string: str):
        pass


    @abstractmethod
    def length_squared(self) -> float:
        pass


    @abstractmethod
    def normalize(self):
        pass


    @abstractmethod
    def dot(self, other):
        pass


    @abstractmethod
    def cross(self, other):
        pass


    def length(self) -> float:
        return math.sqrt(self.length_squared())


    def from_string(self, string: str):
        scomps = string.replace(" ", "").split(",")
        self.from_list([float(s) for s in scomps])


class Coord2d(Coord):
    def __init__(self, x_val:float=0.0, y_val: float=0.0):
        self.x = x_val
        self.y = y_val


    def __repr__(self) -> str:
        return f"{self.x}, {self.y}"


    def __str__(self) -> str:
        return f"{self.x:.3f}, {self.y:.3f}"


    def __add__(self, other):
        return Coord2d(self.x + other.x, self.y + other.y)


    def __sub__(self, other):
        return Coord2d(self.x - other.x, self.y - other.y)
        

    def __mul__(self, other):
        if type(other) is Coord2d:
            return Coord2d(self.x * other.x, self.y * other.y)
        else:
            return Coord2d(self.x * other, self.y * other)


    def length_squared(self) -> float:
        return self.x*self.x + self.y*self.y


    def normalize(self):
        len = self.length()
        self.x /= len
        self.y /= len


    def dot(self, other):
        return self.x * other.x + self.y * other.y


    def cross(self, other):
        return Coord2d((self.x * other.y) - (self.y * other.x), (self.y * other.x) - (self.x * other.y))


    def to_list(self) -> list:
        return [self.x, self.y]


    def from_list(self, coord_list: list):
        if len(coord_list) > 1:
            self.x = coord_list[0]
            self.y = coord_list[1]


class Coord3d(Coord):
    def __init__(self, x_val:float=0.0, y_val: float=0.0, z_val=0.0):
        self.x = x_val
        self.y = y_val
        self.z = z_val


    def __repr__(self) -> str:
        return f"{self.x}, {self.y}, {self.z}"


    def __str__(self) -> str:
        return f"{self.x:.3f}, {self.y:.3f}, {self.z:.3f}"


    def __add__(self, other):
        return Coord3d(self.x + other.x, self.y + other.y, self.z + other.z)


    def __sub__(self, other):
        return Coord3d(self.x - other.x, self.y - other.y, self.z - other.z)


    def __mul__(self, other):
        if type(other) is Coord3d:
            return Coord3d(self.x * other.x, self.y * other.x, self.z * other.z)
        else:
            return Coord3d(self.x * other, self.y * other, self.z * other)


    def to_list(self) -> list:
        return [self.x, self.y, self.z]


    def length_squared(self) -> float:
        return self.x*self.x + self.y*self.y + self.z*self.z


    def normalize(self):
        len = self.length()
        self.x /= len
        self.y /= len
        self.z /= len


    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z


    def cross(self, other):
        return Coord3d(((self.y * other.z) - (self.z * other.y)),  ((self.z * other.x) - (self.x * other.z)), ((self.x * other.y) - (self.y * other.x)))


    def from_list(self, coord_list: list):
        if len(coord_list) > 1:
            self.x = coord_list[0]
            self.y = coord_list[1]
            self.z = coord_list[2]
