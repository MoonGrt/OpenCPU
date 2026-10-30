"""Compile the IDE's integer language to the documented OpenCPU ISA v2 ABI.

Variables occupy 16-bit words. r5 is the frame pointer, r6 the return address,
and r7 a downward-growing stack. Only r1-r4 are caller-saved temporaries.
"""
import ast
from .parser import Assign, Call, For, Function, If, Parser, Print, Return, While


class CompileError(ValueError):
    pass


class Compiler:
    def __init__(self):
        self.functions = {}
        self.variable_offsets = {}
        self._counter = 0
        self._lines = []

    def _emit(self, operation, *operands):
        self._lines.append('    ' + operation + (' ' + ', '.join(map(str, operands)) if operands else ''))

    def _label(self, name):
        self._lines.append(name + ':')

    def _new_label(self, kind):
        self._counter += 1
        return f'.L_{kind}_{self._counter}'

    def _adjust(self, register, amount):
        while amount:
            part = max(-128, min(127, amount))
            self._emit('addi', register, part)
            amount -= part

    def _slot(self, operation, register, name):
        offset = self._slots[name]
        if -16 <= offset <= 15:
            self._emit(operation, register, f'{offset}(fp)')
        else:
            scratch = 'a3' if register == 'a4' else 'a4'
            self._emit('mov', scratch, 'fp')
            self._adjust(scratch, offset)
            self._emit(operation, register, f'0({scratch})')

    def _push(self, register):
        self._emit('addi', 'sp', -1)
        self._emit('sw', register, '0(sp)')

    def _pop(self, register):
        self._emit('lw', register, '0(sp)')
        self._emit('addi', 'sp', 1)

    def _pair(self, left, right, target='a1'):
        other = 'a2' if target == 'a1' else 'a1'
        self._expr(left, target)
        self._push(target)
        self._expr(right, other)
        self._pop(target)
        return other

    def _expr(self, node, target='a1'):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            if not -32768 <= node.value <= 65535:
                raise CompileError('Integer literal must fit in 16 bits')
            self._emit('li', target, node.value)
        elif isinstance(node, ast.Name):
            self._slot('lw', target, node.id)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd, ast.Invert)):
            if (isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant)
                    and type(node.operand.value) is int and 0 <= node.operand.value <= 65535):
                self._expr(ast.Constant((-node.operand.value) & 0xFFFF), target)
                return
            self._expr(node.operand, target)
            if isinstance(node.op, (ast.USub, ast.Invert)):
                self._emit('xori', target, 255)
                other = 'a2' if target == 'a1' else 'a1'
                self._emit('lui', other, 255)
                self._emit('xor', target, other)
                if isinstance(node.op, ast.USub):
                    self._emit('addi', target, 1)
        elif isinstance(node, ast.BinOp):
            operations = {ast.Add: 'add', ast.Sub: 'sub', ast.Mult: 'mul',
                          ast.BitAnd: 'and', ast.BitOr: 'or', ast.BitXor: 'xor',
                          ast.LShift: 'sll', ast.RShift: 'srl'}
            operation = operations.get(type(node.op))
            if operation is None:
                raise CompileError('Unsupported integer operator (division/modulo are not implemented)')
            other = self._pair(node.left, node.right, target)
            self._emit(operation, target, other)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in self.functions:
                raise CompileError(f'Unknown function: {name}')
            parameters = self.functions[name][0]
            if node.keywords or len(node.args) != len(parameters):
                raise CompileError(f'{name} expects {len(parameters)} arguments')
            for argument in node.args:
                self._expr(argument, 'a1')
                self._push('a1')
            for index in range(len(node.args)):
                self._emit('lw', f'a{index + 1}', f'{len(node.args) - index - 1}(sp)')
            self._adjust('sp', len(node.args))
            self._emit('call', name)
            if target != 'a1':
                self._emit('mov', target, 'a1')
        elif isinstance(node, ast.Compare):
            yes, no, end = (self._new_label(kind) for kind in ('true', 'false', 'value'))
            self._condition(node, yes, no)
            self._label(yes)
            self._emit('li', target, 1)
            self._emit('j', end)
            self._label(no)
            self._emit('li', target, 0)
            self._label(end)
        else:
            raise CompileError('Unsupported expression; only 16-bit integers are supported')

    def _condition(self, node, yes, no):
        if isinstance(node, ast.Compare):
            if len(node.ops) != 1:
                raise CompileError('Chained comparisons are not supported')
            self._pair(node.left, node.comparators[0])
            operation = node.ops[0]
            if isinstance(operation, ast.Eq):
                self._emit('beq', 'a1', 'a2', yes)
            elif isinstance(operation, ast.NotEq):
                self._emit('beq', 'a1', 'a2', no)
                self._emit('j', yes)
                return
            elif isinstance(operation, ast.Lt):
                self._emit('blt', 'a1', 'a2', yes)
            elif isinstance(operation, ast.Gt):
                self._emit('blt', 'a2', 'a1', yes)
            elif isinstance(operation, ast.LtE):
                self._emit('blt', 'a2', 'a1', no)
                self._emit('j', yes)
                return
            elif isinstance(operation, ast.GtE):
                self._emit('blt', 'a1', 'a2', no)
                self._emit('j', yes)
                return
            else:
                raise CompileError('Unsupported comparison')
            self._emit('j', no)
        else:
            self._expr(node)
            self._emit('beq', 'a1', 'zero', no)
            self._emit('j', yes)

    def _collect(self, statements, names):
        def expression(node):
            calls = {id(item.func) for item in ast.walk(node) if isinstance(item, ast.Call)}
            for item in ast.walk(node):
                if isinstance(item, ast.Name) and id(item) not in calls and item.id not in names:
                    names.append(item.id)
        for statement in statements:
            if isinstance(statement, Assign):
                if statement.name not in names:
                    names.append(statement.name)
                expression(statement.value)
            elif isinstance(statement, (Call, Return, Print)):
                expression(statement.value)
            elif isinstance(statement, If):
                expression(statement.condition)
                self._collect(statement.body, names)
                self._collect(statement.otherwise, names)
            elif isinstance(statement, While):
                expression(statement.condition)
                self._collect(statement.body, names)
            elif isinstance(statement, For):
                expression(statement.condition)
                self._collect([item for item in (statement.initial, statement.update) if item], names)
                self._collect(statement.body, names)
            elif isinstance(statement, Function):
                raise CompileError('Nested functions are not supported')

    def _statements(self, statements):
        for statement in statements:
            if isinstance(statement, Assign):
                self._expr(statement.value)
                self._slot('sw', 'a1', statement.name)
            elif isinstance(statement, Call):
                self._expr(statement.value)
            elif isinstance(statement, Return):
                self._expr(statement.value)
                self._emit('j', self._return_label)
            elif isinstance(statement, Print):
                raise CompileError('print has no ISA v2 runtime implementation; use explicit MMIO assembly')
            elif isinstance(statement, If):
                yes, no, end = (self._new_label(name) for name in ('if', 'else', 'endif'))
                self._condition(statement.condition, yes, no)
                self._label(yes)
                self._statements(statement.body)
                self._emit('j', end)
                self._label(no)
                self._statements(statement.otherwise)
                self._label(end)
            elif isinstance(statement, (While, For)):
                if isinstance(statement, For) and statement.initial:
                    self._statements([statement.initial])
                test, enter, end = (self._new_label(name) for name in ('loop', 'body', 'endloop'))
                self._label(test)
                self._condition(statement.condition, enter, end)
                self._label(enter)
                self._statements(statement.body)
                if isinstance(statement, For) and statement.update:
                    self._statements([statement.update])
                self._emit('j', test)
                self._label(end)
            else:
                raise CompileError(f'Unsupported statement: {type(statement).__name__}')

    def _function(self, name, parameters, statements, entry=False):
        names = list(parameters)
        self._collect(statements, names)
        if len(names) > 1000:
            raise CompileError('Function frame exceeds the configured 1024-word RAM')
        self._slots = {variable: -index - 1 for index, variable in enumerate(names)}
        if entry:
            self.variable_offsets = dict(self._slots)
        self._return_label = self._new_label('return')
        self._label(name)
        if entry:
            self._emit('li', 'sp', 1024)
            self._emit('li', 'fp', 0)
        self._emit('addi', 'sp', -2)
        self._emit('sw', 'ra', '1(sp)')
        self._emit('sw', 'fp', '0(sp)')
        self._emit('mov', 'fp', 'sp')
        self._adjust('sp', -len(names))
        for index, parameter in enumerate(parameters):
            self._slot('sw', f'a{index + 1}', parameter)
        self._emit('li', 'a1', 0)
        for variable in names[len(parameters):]:
            self._slot('sw', 'a1', variable)
        self._statements(statements)
        if not entry:
            self._emit('li', 'a1', 0)
        self._label(self._return_label)
        if entry:
            self._emit('halt')
        else:
            self._emit('mov', 'sp', 'fp')
            self._emit('lw', 'fp', '0(sp)')
            self._emit('lw', 'ra', '1(sp)')
            self._emit('addi', 'sp', 2)
            self._emit('ret')
        return names

    def compile(self, source: str) -> str:
        """Compile one independent source document to ISA v2 assembly."""
        try:
            return self._compile_source(source)
        except RecursionError:
            raise CompileError('Source nesting exceeds the simple compiler limit') from None

    def _compile_source(self, source: str) -> str:
        self.functions = {}
        self.variable_offsets = {}
        self._counter = 0
        self._lines = []
        main = []
        functions = []
        for statement in Parser().parse(source):
            if isinstance(statement, Function):
                if statement.name == 'main' or statement.name in self.functions:
                    raise CompileError(f'Duplicate/reserved function name: {statement.name}')
                self.functions[statement.name] = (statement.parameters, statement.body)
                functions.append(statement)
            else:
                main.append(statement)
        self._function('main', [], main, entry=True)
        for function in functions:
            self._function(function.name, function.parameters, function.body)
        return '\n'.join(self._lines) + '\n'
