#!/usr/bin/env python3
"""Seeded simulator pressure checks, separate from default unittest discovery.

Run from any directory. The JSON summary and complete failed-case descriptions
are written under --output; --replay re-executes a saved failure without fuzzing.
Only Python's standard library and the pure OpenCPU core are required.
"""
import argparse
from collections import Counter
import gc
import json
from pathlib import Path
import platform
import random
import sys
import time
import tracemalloc

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / 'software'))
from opencpu.core.peripherals import PeripheralModel
from opencpu.core.simulator import Simulator

# Independent specification constants: do not derive the oracle from simulator
# decoder helpers or evaluate generated instructions with a second Simulator.
OPS = dict(add=0, sub=1, mul=2, **{'and': 3, 'or': 4, 'xor': 5}, sll=6, srl=7,
           beq=8, blt=9, halt=10, mret=11, lui=12, j=13, addi=16, subi=17,
           muli=18, andi=19, ori=20, xori=21, slli=22, srli=23, lw=24, sw=25,
           csrr=26, csrw=27, jal=28, jr=29, li=30, rc=31)
R = ('add', 'sub', 'mul', 'and', 'or', 'xor', 'sll', 'srl')
IMM = ('addi', 'subi', 'muli', 'andi', 'ori', 'xori', 'slli', 'srli', 'li', 'lui')


class Failure(AssertionError):
    def __init__(self, message, **details):
        super().__init__(message)
        self.details = details


def equal(actual, expected, message):
    if actual != expected:
        raise Failure(message, expected=expected, actual=actual)


def signed16(value):
    return value if value < 32768 else value - 65536


def encode(op):
    name, rd, rs, immediate = op['name'], op.get('rd', 0), op.get('rs', 0), op.get('imm', 0)
    code = OPS[name] | rd << 5
    if name in R:
        return code | rs << 8
    if name in ('lw', 'sw', 'beq', 'blt'):
        return code | rs << 8 | (immediate & 31) << 11
    if name in ('csrr', 'csrw'):
        return code | immediate << 11
    if name == 'j':
        return OPS[name] | (immediate & 2047) << 5
    if name in ('halt', 'mret', 'rc'):
        return OPS[name]
    return code | (immediate & 255) << 8


def isa_case(rng, length=64):
    names = list(R + IMM + ('lw', 'sw', 'beq', 'blt', 'j', 'jal', 'jr', 'csrr', 'csrw')) * 4 + ['rc']
    registers = [0] + [rng.randrange(65536) for _ in range(7)]
    registers[6], registers[7] = 64, rng.randrange(16)
    memory = {address: rng.randrange(65536) for address in range(96) if rng.randrange(4) == 0}
    operations = []
    for pc in range(length):
        name = rng.choice(names)
        skip = rng.randrange(min(4, length - pc))
        op = {'name': name, 'rd': rng.randrange(6), 'rs': rng.randrange(8), 'imm': 0}
        if name in ('sll', 'srl'):
            op['rs'] = 7  # Reserved count register is always a legal 0..15.
        elif name in ('slli', 'srli'):
            op['imm'] = rng.randrange(16)
        elif name in ('addi', 'subi', 'muli'):
            op['imm'] = rng.randrange(-128, 128)
        elif name in ('andi', 'ori', 'xori', 'li', 'lui'):
            op['imm'] = rng.randrange(256)
        elif name in ('lw', 'sw'):
            op['rs'], op['imm'] = 6, rng.randrange(-16, 16)
        elif name in ('beq', 'blt', 'j', 'jal'):
            op['imm'] = skip
        elif name == 'jr':
            op['rd'], op['imm'] = 0, pc + 1 + skip
        elif name in ('csrr', 'csrw'):
            op['imm'] = rng.randrange(32)
        operations.append(op)
    operations.append({'name': 'halt'})
    return {'registers': registers, 'memory': memory, 'operations': operations,
            'words': [encode(op) for op in operations]}


def oracle(case):
    registers = list(case['registers'])
    memory = {int(address): value for address, value in case['memory'].items()}
    csr, pc, retired, trace = {address: 0 for address in range(2, 8)}, 0, 0, []
    operations = case['operations']
    while retired <= len(operations):
        op = operations[pc]
        name, rd, rs, imm = op['name'], op.get('rd', 0), op.get('rs', 0), op.get('imm', 0)
        a, b, following = registers[rd], registers[rs], pc + 1
        result = None
        if name in R:
            functions = {'add': lambda: a + b, 'sub': lambda: a - b, 'mul': lambda: a * b,
                         'and': lambda: a & b, 'or': lambda: a | b, 'xor': lambda: a ^ b,
                         'sll': lambda: a << b if b < 16 else 0,
                         'srl': lambda: a >> b if b < 16 else 0}
            result = functions[name]()
        elif name in IMM:
            functions = {'addi': lambda: a + imm, 'subi': lambda: a - imm, 'muli': lambda: a * imm,
                         'andi': lambda: a & imm, 'ori': lambda: a | imm, 'xori': lambda: a ^ imm,
                         'slli': lambda: a << imm, 'srli': lambda: a >> imm,
                         'li': lambda: imm, 'lui': lambda: imm * 256}
            result = functions[name]()
        elif name in ('lw', 'sw'):
            address = (b + imm) % 65536
            mapped = address < 1024
            if name == 'lw':
                result = memory.get(address, 0) if mapped else 0
            elif mapped:
                memory[address] = a
        elif name == 'csrr':
            result = retired % 65536 if imm == 0 else retired // 65536 if imm == 1 else csr.get(imm, 0)
        elif name == 'csrw':
            if 2 <= imm <= 7:
                csr[imm] = a
        elif name == 'rc':
            registers = [0] * 8
        elif name == 'beq':
            following += imm if a == b else 0
        elif name == 'blt':
            following += imm if signed16(a) < signed16(b) else 0
        elif name == 'j':
            following += imm
        elif name == 'jal':
            result, following = following, following + imm
        elif name == 'jr':
            following = a + imm
        elif name != 'halt':
            raise Failure('oracle operation unsupported', operation=op)
        if result is not None and rd:
            registers[rd] = result % 65536
        registers[0] = 0
        trace.append({'pc': pc, 'instruction': case['words'][pc], 'next_pc': following,
                      'registers': list(registers), 'csrs': [csr[i] for i in range(2, 8)], 'irq_ack': 0})
        pc, retired = following, retired + 1
        if name == 'halt':
            return registers, memory, csr, pc, trace
    raise Failure('generated forward program did not terminate')


def run_isa_case(case):
    registers, memory, csr, pc, expected_trace = oracle(case)
    model = Simulator(history_limit=0)
    model.registers = list(case['registers'])
    model.data_mem = {int(address): value for address, value in case['memory'].items()}
    model.inst_mem = case['words']
    index = 0
    def inspect(record):
        nonlocal index
        expected = expected_trace[index]
        for key, value in expected.items():
            equal(record[key], value, f'ISA retirement {index} {key}')
        index += 1
    model.run(len(case['words']) * 2, trace=inspect)
    equal((model.halted, model.faulted, model.pc), (True, False, pc), 'ISA final control')
    equal(model.registers, registers, 'ISA final registers')
    equal(model.data_mem, memory, 'ISA final RAM')
    equal([model.read_csr(i) for i in range(2, 8)], [csr[i] for i in range(2, 8)], 'ISA final CSR')
    equal(model.instructions_retired, len(expected_trace), 'ISA retired count')
    equal(model.cycle, len(expected_trace), 'ISA logical ticks')
    return {'instructions': index, 'opcodes': [op['name'] for op in case['operations']]}


def transaction_case(rng):
    actions = []
    names = ('step', 'step', 'step', 'rx', 'inputs', 'ticks', 'irq', 'read', 'peek')
    for _ in range(rng.randrange(12, 36)):
        name = rng.choice(names)
        if name == 'step':
            action = [name, rng.choice((0, 0, 0, 1, 2, 3))]
        elif name == 'rx':
            action = [name, [rng.randrange(256) for _ in range(rng.randrange(12))], rng.randrange(10) == 0]
        elif name == 'inputs':
            action = [name, rng.randrange(16), rng.randrange(16)]
        elif name == 'ticks':
            action = [name, rng.randrange(65)]
        elif name == 'irq':
            action = [name, rng.randrange(256)]
        else:
            action = [name]
        actions.append(action)
    return {'fifo_depth': rng.randrange(1, 9), 'frame_ticks': rng.randrange(1, 12),
            'period': rng.randrange(1, 20), 'value': rng.randrange(65536), 'actions': actions}


def transaction_model(case):
    device = PeripheralModel(fifo_depth=case['fifo_depth'], uart_frame_ticks=case['frame_ticks'])
    model = Simulator(history_limit=None, peripherals=device)
    # Straight-line word bus operations and a returning interrupt handler.
    model.inst_mem = {0: 24 | 2 << 5 | 6 << 8, 1: 25 | 1 << 5 | 6 << 8,
                      2: 16 | 1 << 5 | 1 << 8, 3: 25 | 1 << 5 | 5 << 8,
                      4: 24 | 3 << 5 | 5 << 8, 5: 13 | 2042 << 5,
                      16: 26 | 4 << 5 | 3 << 11, 17: 11}
    model.registers[1], model.registers[5], model.registers[6] = case['value'], 32, 0xff40
    model.write_csr(2, 16)
    model.write_csr(5, 3)
    model.write_csr(6, 8)
    device.write(0xff50, case['period'])
    device.write(0xff52, 3)
    model.advance_ticks(1)  # Consume reconfiguration before independent time checks.
    model.clear_history()
    return model


def do_transaction(model, action):
    before = model.snapshot()
    name = action[0]
    if name == 'step':
        registers = list(before['registers'])
        old_pc = before['pc']
        following = old_pc + 1
        if old_pc == 0:
            registers[2] = before['peripherals']['uart']['rx'][0] if before['peripherals']['uart']['rx'] else 0
        elif old_pc == 2:
            registers[1] = (registers[1] + 1) % 65536
        elif old_pc == 4:
            registers[3] = before['data_mem'].get(32, 0)
        elif old_pc == 5:
            following = 0
        elif old_pc == 16:
            registers[4] = before['csr'][3]
        elif old_pc == 17:
            following = before['csr'][4]
        elif old_pc not in (1, 3):
            raise Failure('unexpected transaction program PC', pc=old_pc)
        eligible = (before['pending_interrupts'] | action[1]) & before['csr'][5] & 255
        selected = (eligible & -eligible) if eligible and before['csr'][6] & 8 and not before['in_interrupt'] and old_pc != 17 else 0
        normal_pc = following
        if selected:
            following = before['csr'][2]
        equal(model.step(irq=action[1]), True, 'transaction instruction must retire')
        equal(model.registers, registers, 'transaction independent instruction result')
        equal(model.pc, following, 'transaction independent next PC')
        equal(model.last_retire['irq_ack'], selected, 'transaction IRQ priority')
        expected_status = before['csr'][6]
        expected_in_isr = before['in_interrupt']
        if old_pc == 17:
            expected_status = (expected_status & ~8) | (8 if expected_status & 128 else 0) | 128
            expected_in_isr = False
        elif selected:
            expected_status = (expected_status & ~(8 | 128)) | (128 if expected_status & 8 else 0)
            expected_in_isr = True
            equal(model.read_csr(4), normal_pc, 'IRQ saves independent real next PC')
            equal(model.read_csr(3), selected.bit_length() - 1, 'IRQ cause')
        equal(model.read_csr(6), expected_status, 'IRQ/MRET status transition')
        equal(model.in_interrupt, expected_in_isr, 'IRQ/MRET nesting state')
        if old_pc == 3:
            equal(model.data_mem.get(32), before['registers'][1], 'transaction independent store')
        expected_retired, expected_ticks = before['instructions_retired'] + 1, 1
    elif name == 'rx':
        model.inject_uart(action[1], framing_error=action[2])
        expected_rx = list(before['peripherals']['uart']['rx'])
        if not action[2]:
            expected_rx.extend(action[1][:model.peripherals.fifo_depth - len(expected_rx)])
        equal(model.peripherals.snapshot()['uart']['rx'], expected_rx, 'bounded RX FIFO order')
        expected_retired, expected_ticks = before['instructions_retired'], 0
    elif name == 'inputs':
        model.set_inputs(buttons=action[1], switches=action[2])
        equal((model.peek_data(0xff10), model.peek_data(0xff20)), tuple(action[1:]), 'external GPIO values')
        expected_retired, expected_ticks = before['instructions_retired'], 0
    elif name == 'ticks':
        model.advance_ticks(action[1])
        timer = before['peripherals']['timer']
        equal(model.peripherals.snapshot()['timer']['counter'],
              (timer['counter'] + action[1]) % timer['period'], 'independent periodic timer progression')
        expected_retired, expected_ticks = before['instructions_retired'], action[1]
    elif name == 'irq':
        model.request_interrupt(action[1])
        equal(model.pending_interrupts, before['pending_interrupts'] | action[1], 'latched event mask')
        expected_retired, expected_ticks = before['instructions_retired'], 0
    elif name == 'read':
        rx = before['peripherals']['uart']['rx']
        equal(model.read_data(0xff40, side_effects=True), rx[0] if rx else 0, 'RX consuming read')
        equal(model.peripherals.snapshot()['uart']['rx'], rx[1:], 'RX consuming FIFO order')
        expected_retired, expected_ticks = before['instructions_retired'], 0
    else:
        model.peek_data(0xff40)
        model.read_data(0xff41)
        equal(model.snapshot(), before, 'debug peek cannot mutate state')
        expected_retired, expected_ticks = before['instructions_retired'], 0
    equal(model.instructions_retired, expected_retired, 'event retirement counter')
    equal(model.cycle, (before['cycle'] + expected_ticks) % (1 << 32), 'event cycle counter')
    equal(model.peripherals.ticks, before['peripherals']['ticks'] + expected_ticks, 'event device time')


def run_transaction_case(case):
    model = transaction_model(case)
    start = model.snapshot()
    for action in case['actions']:
        do_transaction(model, action)
    end, events = model.snapshot(), model.history_size
    for _ in range(events):
        equal(model.run_undo(), True, 'transaction undo available')
    equal(model.snapshot(), start, 'transaction full rewind')
    equal(model.can_undo, False, 'transaction history drained')
    for action in case['actions']:
        do_transaction(model, action)
    equal(model.snapshot(), end, 'transaction deterministic replay')
    return {'actions': len(case['actions']), 'undo_events': events, 'instructions': model.instructions_retired}


def bulk_case(rng):
    actions = []
    for _ in range(24):
        choice = rng.randrange(7)
        if choice == 0:
            actions.append(['ticks', rng.randrange(120)])
        elif choice == 1:
            actions.append(['rx', [rng.randrange(256) for _ in range(rng.randrange(12))], rng.randrange(16) == 0])
        elif choice == 2:
            actions.append(['read', rng.choice((0xff40, 0xff41, 0xff42, 0xff53, 0xff55))])
        elif choice == 3:
            actions.append(['inputs', rng.randrange(16), rng.randrange(16)])
        else:
            address = rng.choice((0xff00, 0xff30, 0xff40, 0xff42, 0xff50, 0xff51, 0xff52, 0xff55))
            value = rng.randrange(32) if address in (0xff50, 0xff51) else rng.randrange(65536)
            actions.append(['write', address, value])
    # Every sequence has nontrivial bulk work, independent of random choices.
    actions.append(['ticks', rng.randrange(1, 120)])
    return {'fifo_depth': rng.randrange(1, 17), 'frame_ticks': rng.randrange(1, 21), 'actions': actions}


def run_bulk_case(case):
    bulk = PeripheralModel(fifo_depth=case['fifo_depth'], uart_frame_ticks=case['frame_ticks'])
    single = PeripheralModel(fifo_depth=case['fifo_depth'], uart_frame_ticks=case['frame_ticks'])
    ticks = 0
    for index, action in enumerate(case['actions']):
        name = action[0]
        if name == 'ticks':
            actual, expected = bulk.tick(action[1]), 0
            for _ in range(action[1]):
                expected |= single.tick()
            equal(actual, expected, f'bulk/single tick IRQ at {index}')
            ticks += action[1]
        elif name == 'read':
            equal(bulk.read(action[1]), single.read(action[1]), f'bulk/single consuming read {index}')
        else:
            for device in (bulk, single):
                if name == 'rx':
                    device.inject_uart(action[1], framing_error=action[2])
                elif name == 'inputs':
                    device.set_inputs(action[1], action[2])
                else:
                    device.write(action[1], action[2])
        equal(bulk.snapshot(), single.snapshot(), f'bulk/single complete state after action {index}')
    return {'actions': len(case['actions']), 'single_ticks': ticks}


def fault_case(rng):
    kind = rng.choice(('illegal', 'fetch', 'breakpoint', 'halt', 'stop'))
    prefix = rng.randrange(1, 20)
    invalid = rng.choice((14, 15, 0x8000, 0x002a, 0x0100 | 26, 0x002b, 0x003f))
    return {'kind': kind, 'prefix': prefix, 'invalid': invalid}


def run_fault_case(case):
    kind, prefix = case['kind'], case['prefix']
    model = Simulator(history_limit=None)
    model.inst_mem = [16 | 1 << 5 | 1 << 8] * prefix
    if kind == 'illegal':
        model.inst_mem.append(case['invalid'])
    elif kind == 'fetch':
        model.inst_mem.append(13 | ((1024 - prefix - 1) & 2047) << 5)
    else:
        model.inst_mem.append(10)
    if kind == 'breakpoint':
        model.breakpoints = {prefix}
        equal(model.run(prefix + 4), prefix, 'breakpoint prefix count')
        equal((model.stop_reason, model.breakpoint_hit), ('breakpoint', prefix), 'breakpoint stop reason')
        equal(model.run(1), 1, 'breakpoint continue executes terminal HALT once')
    elif kind == 'stop':
        model.run(prefix)
        before = model.snapshot()
        model.stop()
        equal(model.step(), False, 'explicit stop suppresses step')
        equal(model.run(1), 1, 'explicit stop resumes on run')
        equal(model.registers[1], prefix, 'stopped register value')
        equal(before['instructions_retired'], prefix, 'stopped prefix count')
    else:
        model.run(prefix)
        before = model.snapshot()
        if kind == 'fetch':
            equal(model.step(), True, 'out-of-ROM branch retires')
            before = model.snapshot()
        if kind == 'halt':
            equal(model.step(), True, 'HALT retires')
            equal(model.stop_reason, 'halt', 'HALT reason')
        else:
            equal(model.step(), False, 'invalid path does not retire')
            equal(model.fault_code, 1 if kind == 'illegal' else 2, 'structured fault code')
            equal(model.instructions_retired, before['instructions_retired'], 'fault does not retire')
            equal(model.cycle, before['cycle'], 'fault does not advance time')
        after = model.snapshot()
        equal(model.step(), False, 'terminal state rejects later steps')
        equal(model.snapshot(), after, 'terminal step is inert')
        equal(model.run_undo(), True, 'terminal event can be undone')
        equal(model.snapshot(), before, 'terminal undo leaves preceding instruction intact')
        model.step()
        equal(model.snapshot(), after, 'terminal event deterministically replays')
    return {'paths': 1}


def run_long_case(case):
    steps, history_limit = case['steps'], case['history_limit']
    gc.collect()
    tracemalloc.start()
    started = time.perf_counter()
    try:
        model = Simulator(history_limit=history_limit)
        model.inst_mem = [16 | 1 << 5 | 1 << 8, 13 | 2046 << 5]
        warm = min(2000, steps)
        points = [warm, max(warm, steps // 2), steps]
        samples, done = [], 0
        for target in points:
            if target > done:
                equal(model.run(target - done), target - done, 'long-loop run budget')
                done = target
            gc.collect()
            current, peak = tracemalloc.get_traced_memory()
            samples.append({'instructions': done, 'current_bytes': current, 'peak_bytes': peak})
            equal(model.registers[1], ((done + 1) // 2) % 65536, 'long-loop independent arithmetic')
            equal(model.pc, done % 2, 'long-loop PC')
            equal(model.instructions_retired, done, 'long-loop retirement count')
            equal(model.cycle, done % (1 << 32), 'long-loop cycle count')
            equal(model.history_size, min(history_limit, done), 'bounded long-loop history')
        duration = time.perf_counter() - started
        equal((model.stop_reason, model.limit_reached), ('limit', True), 'long-loop stop state')
        growth = samples[-1]['current_bytes'] - samples[0]['current_bytes']
        # Excludes timing-dependent RSS, allocator arenas, and unrelated tasks.
        # A leaked per-instruction snapshot would exceed this by orders of magnitude.
        if growth > 256 * 1024:
            raise Failure('long-loop retained memory grows after warmup', samples=samples, growth_bytes=growth)
        if samples[-1]['peak_bytes'] > 32 * 1024 * 1024:
            raise Failure('long-loop peak exceeds bounded-history budget', samples=samples)
        return {'instructions': steps, 'history_limit': history_limit,
                'duration_seconds': duration, 'instructions_per_second': steps / duration,
                'retained_growth_bytes': growth, 'samples': samples,
                'measurement': {'tracemalloc_enabled': True,
                                'scope': 'Python allocations in the tested process; not RSS',
                                'sampling_overhead_included': True,
                                'speed': 'local traced observation; not a timing acceptance threshold'}}
    finally:
        tracemalloc.stop()


RUNNERS = {'random_isa': run_isa_case, 'undo_replay': run_transaction_case,
           'peripheral_bulk': run_bulk_case, 'terminal_states': run_fault_case,
           'long_run': run_long_case}


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be positive')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=20261030)
    parser.add_argument('--cases', type=positive, default=1000, help='cases in each randomized category')
    parser.add_argument('--steps', type=positive, default=1000000, help='instructions per long-run history configuration')
    parser.add_argument('--output', type=Path, default=REPOSITORY / 'build/stress/latest/simulator')
    parser.add_argument('--replay', type=Path, help='replay one saved failure JSON')
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    summary = {'schema_version': 1, 'component': 'simulator', 'seed': args.seed, 'passed': False,
               'failed': 0, 'duration_seconds': 0, 'categories': {}, 'failures': [],
               'configuration': {'cases_per_category': args.cases, 'steps_per_history': args.steps,
                                 'random_program_length': 64},
               'environment': {'python': platform.python_version(), 'platform': platform.platform()},
               'oracle': {'random_isa': 'independent symbolic Python operations and every retirement',
                          'undo_replay': 'independent CPU/counter/IRQ/FIFO checks plus rewind/replay',
                          'peripheral_bulk': 'metamorphic bulk tick versus repeated single tick',
                          'terminal_states': 'explicit halt/fault/breakpoint/stop expectations'}}
    started = time.perf_counter()
    def save():
        summary['duration_seconds'] = time.perf_counter() - started
        temporary = args.output / 'summary.tmp.json'
        temporary.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
        temporary.replace(args.output / 'summary.json')
    def execute(category, index, case):
        try:
            return RUNNERS[category](case)
        except Exception as error:
            failure = {'category': category, 'index': index, 'seed': summary['seed'], 'case': case,
                       'error': str(error), 'details': getattr(error, 'details', {})}
            directory = args.output / 'replay'
            directory.mkdir(exist_ok=True)
            path = directory / f'{category}-{index:05d}.json'
            path.write_text(json.dumps(failure, indent=2, sort_keys=True, default=repr) + '\n')
            summary['failed'] += 1
            summary['failures'].append({'category': category, 'index': index,
                                        'replay': str(path.resolve()), 'error': str(error)})
            return None
    try:
        if args.replay:
            failure = json.loads(args.replay.read_text())
            summary['seed'] = failure.get('seed', args.seed)
            result = execute(failure['category'], failure['index'], failure['case'])
            summary['categories'][failure['category']] = {'cases': 1, 'metrics': result}
        else:
            rng = random.Random(args.seed)
            for name, generate in (('random_isa', isa_case), ('undo_replay', transaction_case),
                                   ('peripheral_bulk', bulk_case), ('terminal_states', fault_case)):
                category_started = time.perf_counter()
                totals, opcodes = Counter(), Counter()
                completed = 0
                for index in range(args.cases):
                    case = generate(rng)
                    result = execute(name, index, case)
                    if result is None:
                        break
                    for key, value in result.items():
                        if key == 'opcodes':
                            opcodes.update(value)
                        else:
                            totals[key] += value
                    completed += 1
                summary['categories'][name] = {'cases': completed, 'metrics': dict(totals),
                                                'duration_seconds': time.perf_counter() - category_started}
                if opcodes:
                    summary['categories'][name]['opcodes'] = dict(opcodes)
                save()
                if summary['failed']:
                    break
            if not summary['failed']:
                results = []
                for index, history_limit in enumerate((0, 1000)):
                    result = execute('long_run', index, {'steps': args.steps, 'history_limit': history_limit})
                    if result is not None:
                        results.append(result)
                    else:
                        break
                summary['categories']['long_run'] = {'cases': len(results), 'metrics': results}
        summary['passed'] = summary['failed'] == 0
        save()
    except Exception as error:
        summary['failed'] += 1
        summary['failures'].append({'error': str(error)})
        save()
    print(json.dumps({'passed': summary['passed'], 'failed': summary['failed'],
                      'summary': str((args.output / 'summary.json').resolve()),
                      'duration_seconds': summary['duration_seconds']}))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
