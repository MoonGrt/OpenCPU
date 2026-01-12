from Assembler import assembler

# 仿真器
class simulator:
    def __init__(self, start_pc):
        # 初始化寄存器
        self.registers = [0] * 8

        # 程序起始行
        self.start_pc = start_pc
        # 程序计数器
        self.pc = start_pc
        # 下一条指令的程序计数器
        self.last_pc = start_pc
        # 上一条指令的程序计数器
        self.next_pc = start_pc

        self.data_mem = {}
        self.inst_mem = {}

    def update_pc(self, instruction):
        Imm = (instruction >> 8) & 0b11111111
        imm = (instruction >> 11) & 0b11111
        rs = (instruction >> 8) & 0b111
        rd = (instruction >> 5) & 0b111
        opcode = instruction & 0b11111

        self.last_pc = self.pc

        # if imm & 0x10 == 0x10:
        #     imm = imm - 0x20
        # TODO: imm/Imm 负数

        if opcode == 0b00111:  # BEQ
            if self.registers[rd] == self.registers[rs]:
                self.next_pc = imm
                return
        elif opcode == 0b01000:  # BLE
            if self.registers[rd] <= self.registers[rs]:
                self.next_pc = imm
                return
        elif opcode == 0b11010:  # J
            self.next_pc = Imm
            return
        elif opcode == 0b11011:  # JR
            self.next_pc = self.registers[rd]
            return

        # 执行指令并更新下一条指令的程序计数器
        self.next_pc = self.pc + 1

    def execute_instruction(self, instruction):
        Imm = (instruction >> 8) & 0b11111111
        imm = (instruction >> 11) & 0b11111
        rs = (instruction >> 8) & 0b111
        rd = (instruction >> 5) & 0b111
        opcode = instruction & 0b11111

        # if imm & 0x10 == 0x10:
        #     imm = imm - 0x20
        # TODO: imm/Imm 负数
        
        if opcode == 0b00000:  # ADD
            self.registers[rd] += self.registers[rs]
        elif opcode == 0b00001:  # SUB
            self.registers[rd] -= self.registers[rs]
        elif opcode == 0b00010:  # AND
            self.registers[rd] &= self.registers[rs]
        elif opcode == 0b00011:  # OR
            self.registers[rd] |= self.registers[rs]
        elif opcode == 0b00100:  # XOR
            self.registers[rd] ^= self.registers[rs]
        elif opcode == 0b00101:  # SLL
            self.registers[rd] <<= self.registers[rd]
        elif opcode == 0b00110:  # SRL
            self.registers[rd] >>= self.registers[rd]

        elif opcode == 0b10000:  # ADDI
            self.registers[rd] += imm
        elif opcode == 0b10001:  # SUBI
            self.registers[rd] -= imm
        elif opcode == 0b10010:  # ANDI
            self.registers[rd] &= imm
        elif opcode == 0b10011:  # ORI
            self.registers[rd] |= imm
        elif opcode == 0b10100:  # XORI
            self.registers[rd] ^= imm
        elif opcode == 0b10101:  # SLLI
            self.registers[rd] <<= self.registers[rd]
        elif opcode == 0b10110:  # SRLI
            self.registers[rd] >>= self.registers[rd]
        elif opcode == 0b10111:  # LW
            address = self.registers[rs] + imm
            self.registers[rd] = self.data_mem.get(address)
        elif opcode == 0b11000:  # SW
            address = self.registers[rs] + imm
            self.data_mem[address] = self.registers[rd]

        elif opcode == 0b11001:  # LI CALL
            self.registers[rd] = Imm

    def run(self):
        # 运行程序
        while self.next_pc < len(self.inst_mem):
            self.update_pc(self.inst_mem[self.next_pc])
            self.execute_instruction(self.inst_mem[self.pc])
            self.pc = self.next_pc

    def run_step(self):
        # 单步运行程序
        if self.next_pc < len(self.inst_mem):
            self.update_pc(self.inst_mem[self.next_pc])
            self.execute_instruction(self.inst_mem[self.pc])
            self.pc = self.next_pc

    def run_undo(self):
        self.pc = self.last_pc

        instruction = self.inst_mem[self.pc]
        Imm = (instruction >> 8) & 0b11111111
        imm = (instruction >> 11) & 0b11111
        rs = (instruction >> 8) & 0b111
        rd = (instruction >> 5) & 0b111
        opcode = instruction & 0b11111

        # 对于 CALL, J, JR, BEQ, BLE 撤销这些指令不需要特定的逻辑
        # 对于其他指令的撤销操作
        if opcode == 0b00000:  # ADD
            self.registers[rd] -= self.registers[rs]
        elif opcode == 0b00001:  # SUB
            self.registers[rd] += self.registers[rs]
        elif opcode == 0b00010:  # AND
            self.registers[rd] &= ~self.registers[rs]
        elif opcode == 0b00011:  # OR
            self.registers[rd] |= ~self.registers[rs]
        elif opcode == 0b00100:  # XOR
            self.registers[rd] ^= ~self.registers[rs]
        elif opcode == 0b00101:  # SLL
            self.registers[rd] >>= self.registers[rd]
        elif opcode == 0b00110:  # SRL
            self.registers[rd] <<= self.registers[rd]
        elif opcode == 0b10000:  # ADDI
            self.registers[rd] -= imm
        elif opcode == 0b10001:  # SUBI
            self.registers[rd] += imm
        elif opcode == 0b10010:  # ANDI
            self.registers[rd] &= ~imm
        elif opcode == 0b10011:  # ORI
            self.registers[rd] |= ~imm
        elif opcode == 0b10100:  # XORI
            self.registers[rd] ^= ~imm
        elif opcode == 0b10101:  # SLLI
            self.registers[rd] >>= self.registers[rd]
        elif opcode == 0b10110:  # SRLI
            self.registers[rd] <<= self.registers[rd]
        elif opcode == 0b10111:  # LW
            pass  # 不需要撤销加载
        elif opcode == 0b11000:  # SW
            pass  # 不需要撤销存储
        elif opcode == 0b11001:  # LI
            pass

    def reset(self):
        # 初始化寄存器
        self.registers = [0] * 8
        # 程序计数器
        self.pc = 0
        # 下一条指令的程序计数器
        self.last_pc = 0
        # 上一条指令的程序计数器
        self.next_pc = 0
        self.data_mem = {}

    def stop(self):
        pass


# 示例用法
if __name__ == "__main__":
    program_code = """
    add:
        addi    sp, sp, -48
        sw      ra, 44(sp)
        sw      s0, 40(sp)
        addi    s0, sp, 48
        sw      a1, -36(s0)
        sw      a2, -40(s0)
        lw      a1, -36(s0)
        lw      a2, -40(s0)
        add     a1, a1, a2
        sw      a1, -20(s0)
        lw      ra, 44(sp)
        lw      s0, 40(sp)
        addi    sp, sp, 48
        jr      ra
    main:
        li      a1, 1
        sw      a1, -20(s0)
        li      a1, 2
        sw      a1, -24(s0)
        lw      a1, -20(s0)
        lw      a2, -24(s0)
        call    add
    """

    Assembler = assembler()
    machine_code = Assembler.assemble(program_code)

    Simulator = simulator(Assembler.getlabel().get('main'))

    # 按行分割并转换为整数列表
    lines = machine_code.strip().split('\n')
    # 将二进制字符串转换为整数
    Simulator.inst_mem = [int(line, 2) for line in lines]

    Simulator.run()

    # 打印寄存器状态
    print(Simulator.registers)
