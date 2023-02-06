from gamejam.coord import Coord3d
from gamejam.quickmaff import MATRIX_IDENTITY

class Camera:
    _speed = 0.125


    def __init__(self):
        self.mat = MATRIX_IDENTITY[:]
        self.pos = Coord3d()
        self.target = Coord3d()


    def look_at(self, target_pos: Coord3d):
        """Refresh the camera matrix by reconstruction"""
        forward = target_pos - self.m_pos
        forward.normalize()
        forward = -forward

        right = forward.cross(Coord3d(0.0, 0.0, 1.0))
        right.normalize()

        up = right.cross(forward)
    
        right = -right
        #self.mat.SetRight(right)
        #self.mat.SetLook(up)
        #self.mat.SetUp(forward)
        #self.mat.SetPos(self.pos)