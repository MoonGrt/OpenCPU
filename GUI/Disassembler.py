# 反汇编器
class disassembler:
    def __init__(self):
        self.opcode_dict = {
            '00000': 'add',      '10000': 'addi',
            '00001': 'sub',      '10001': 'subi',
            '00010': 'mul',      '10010': 'muli',
            '00011': 'and',      '10011': 'andi',
            '00100': 'or',       '10100': 'ori',
            '00101': 'xor',      '10101': 'xori',
            '00110': 'sll',      '10110': 'slli',
            '00111': 'srl',      '10111': 'srli',
            '01000': 'beq',      '11000': 'lw',
            '01001': 'blt',      '11001': 'sw',

            '11010': 'csrr',
            '11011': 'csrw',
            '11100': 'jal',
            '11101': 'jr',
            '11110': 'li',
            '11111': 'rc'
        }
        self.reg_dict = {0: 's0', 1: 'a1', 2: 'a2', 3: 'a3', 4: 'a4', 5: 'a5', 6: 'ra', 7: 'sp'}

    def disassemble(self, machine_code):
        instructions = []
        for line in machine_code.strip().split('\n'):
            line = line.strip()
            if line == '0000000000000000':
                pass
            elif line:
                imm = line[:5]
                IMM = line[:8]
                rs = line[5:8]
                rd = line[8:11]
                opcode = line[11:]
                
                opcode_str = self.opcode_dict.get(opcode, 'unknown')
                if opcode_str in {'add', 'sub', 'and', 'or', 'xor', 'sll', 'srl'}:
                    rs_name = self.reg_dict.get(int(rs, 2), 'unknown')
                    rd_name = self.reg_dict.get(int(rd, 2), 'unknown')
                    imm_val = int(imm, 2)
                    opcode_str = opcode_str.ljust(4)
                    instructions.append(f"{opcode_str} {rd_name}, {rs_name}, {imm_val}")
                elif opcode_str in {'beq', 'blt'}:
                    rd_name = self.reg_dict.get(int(rs, 2), 'unknown')
                    rs_name = self.reg_dict.get(int(rd, 2), 'unknown')
                    imm_val = int(imm, 2)
                    opcode_str = opcode_str.ljust(4)
                    instructions.append(f"{opcode_str} {rd_name}, {rs_name}, {imm_val}")
                elif opcode_str in {'addi', 'subi', 'andi', 'ori', 'xori', 'slli', 'srli'}:
                    rd_name = self.reg_dict.get(int(rd, 2), 'unknown')
                    rs_name = 's0'
                    imm_val = int(imm, 2)
                    opcode_str = opcode_str.ljust(4)
                    instructions.append(f"{opcode_str} {rd_name}, {rs_name}, {imm_val}")
                elif opcode_str in {'lw', 'sw', 'csrr', 'csrw'}:
                    rd_name = self.reg_dict.get(int(rd, 2), 'unknown')
                    imm_val = int(imm, 2)
                    opcode_str = opcode_str.ljust(4)
                    instructions.append(f"{opcode_str} {rd_name}, {imm_val}({self.reg_dict.get(int(rs, 2), 'unknown')})")
                elif opcode_str in {'jal', 'jr', 'li'}:
                    rd_name = self.reg_dict.get(int(rd, 2), 'unknown')
                    imm_val = int(IMM, 2)
                    opcode_str = opcode_str.ljust(4)
                    instructions.append(f"{opcode_str} {rd_name}, {imm_val}")
                elif opcode_str == 'rc':
                    instructions.append(f"{opcode_str}")
                else:
                    instructions.append(f"Unknown opcode {opcode}")
        
        return "\n".join(instructions)

# 测试用例
if __name__ == "__main__":
    machine_code = """
        0000000000011111
        1111111100111110
        0100000000110110
        0001000001011110
        0000000101000000
        0000001001011000
        0000100001011001
        0000100001111000
        0111100001110101
        0000000101111001
        0000000000011100
        0000000000000000
    """
    
    Disassembler = disassembler()
    assembly_code = Disassembler.disassemble(machine_code)
    print(assembly_code)
