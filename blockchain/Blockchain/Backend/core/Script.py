import sys
sys.path.append('/Users/my/Desktop/blockchain')

from Blockchain.Backend.util.util import int_to_little_endian, encode_varint, little_endian_to_int, read_varint
from Blockchain.Backend.core.EllepticCurve.op import OP_CODE_FUNCTION


class Script:
    def __init__(self, cmds=None):
        if cmds is None:
            self.cmds = []
        else:
            self.cmds = cmds

    def __add__(self, other):
        return Script(self.cmds + other.cmds)

    def serialize(self):
        # initialize what we'll send back
        result = b""
        # go through each cmd
        for cmd in self.cmds:
            # if the cmd is an integer, it's an opcode
            if type(cmd) == int:
                # turn the cmd into a single byte integer using int_to_little_endian
                # result += int_to_little_endian(cmd, 1)
                result += int_to_little_endian(cmd, 1)
            else:
                # otherwise, this is an element
                # get the length in bytes
                length = len(cmd)
                # for large lengths, we have to use a pushdata opcode
                if length < 75:
                    # turn the length into a single byte integer
                    result += int_to_little_endian(length, 1)
                elif length > 75 and length < 0x100:
                    # 76 is pushdata1
                    result += int_to_little_endian(76, 1)
                    result += int_to_little_endian(length, 1)
                elif length >= 0x100 and length <= 520:
                    # 77 is pushdata2
                    result += int_to_little_endian(77, 1)
                    result += int_to_little_endian(length, 2)
                else:
                    raise ValueError("too long an cmd")

                result += cmd
        # get the length of the whole thing
        total = len(result)
        # encode_varint the total length of the result and prepend
        return encode_varint(total) + result

    @classmethod
    def parse(cls, s):
        # get the length of the entire field
        length = read_varint(s)
        # initialize the cmds array
        cmds = []
        # initialize the number of bytes we've read to 0
        count = 0
        # loop until we've read length bytes
        while count < length:
            # get the current byte
            current = s.read(1)
            # increment the bytes we've read
            count += 1
            # convert the current byte to an integer
            current_byte = current[0]
            # if the current byte is between 1 and 75 inclusive
            if current_byte >= 1 and current_byte <= 75:
                # we have an cmd set n to be the current byte
                n = current_byte
                # add the next n bytes as an cmd
                cmds.append(s.read(n))
                # increase the count by n
                count += n
            elif current_byte == 76:
                # op_pushdata1
                data_length = little_endian_to_int(s.read(1))
                cmds.append(s.read(data_length))
                count += data_length + 1
            elif current_byte == 77:
                # op_pushdata2
                data_length = little_endian_to_int(s.read(2))
                cmds.append(s.read(data_length))
                count += data_length + 2
            else:
                # we have an opcode. set the current byte to op_code
                op_code = current_byte
                # add the op_code to the list of cmds
                cmds.append(op_code)
        if count != length:
            raise SyntaxError('parsing script failed')
        return cls(cmds)

    def evaluate(self, z):
        cmds = self.cmds[:]
        stack = []

        while len(cmds) > 0:
            cmd = cmds.pop(0)

            if type(cmd) == int:
                operation = OP_CODE_FUNCTION[cmd]

                if cmd == 172:
                    if not operation(stack, z):
                        print(f"Error in Signature Verification")
                        return False

                elif not operation(stack):
                    print(f"Error in Signature Verification")
                    return False
            else:
                stack.append(cmd)
        return True

    @classmethod
    def p2pkh_script(cls, h160):
        """Takes a hash160 and returns the p2pkh ScriptPubKey"""
        return Script([0x76, 0xA9, h160, 0x88, 0xAC])
