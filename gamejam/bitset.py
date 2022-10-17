class BitSet:
    """Convenience class for storing and testing multiple values."""
    def __init__(self):
        self.reset()        


    def reset(self):
        self._bits = 0


    def set_bit(self, bit:int):
        self._bits |= (1 << bit)


    def toggle_bit(self, bit:int):
        self._bits ^= (1 << bit)


    def is_bit_set(self, bit:int) -> bool:
        return (self._bits & (1 << bit)) != 0


    def get_bits(self) -> int:
        return self._bits


    def count_bits(self) -> int:
        n = 0
        b_copy = self._bits
        while b_copy:
            b_copy &= b_copy-1
            n += 1
        return n
