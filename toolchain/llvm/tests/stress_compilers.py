#!/usr/bin/env python3
"""Seeded compiler stress against independent integer oracles and real UART RTL.

Default: 300 simple programs, 250 C programs and 50 UART samples per backend.
Artifacts remain in build/stress/latest/compilers; replay any case with --replay.
No generated program uses a simulator result as its expected language result.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import time
import traceback
import unittest

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / 'software'))
sys.path.insert(0, str(REPOSITORY / 'hardware/common/tb'))
from opencpu.core.compiler.llvm import CProject
from opencpu.core.simulator import Simulator
from opencpu.core.toolchain import Toolchain
from soc_support import SocDriverMixin

MASK = 65535
OPS = ('add', 'sub', 'mul', 'and', 'or', 'xor', 'div', 'rem', 'shl', 'shr')
SYMBOL = dict(add='+', sub='-', mul='*', **{'and': '&', 'or': '|', 'xor': '^', 'div': '/', 'rem': '%', 'shl': '<<', 'shr': '>>'})
EDGES = (0, 1, 2, 7, 15, 16, 127, 128, 255, 256, 32767, 32768, 65534, 65535)
RESOURCE = re.compile(r'(?:exceed[^\n]*(?:ROM|RAM)|(?:ROM|RAM)[^\n]*(?:exceed|capacity)|configured[^\n]*ROM|source nesting exceeds[^\n]*limit)', re.I)


def word(value):
    return value & MASK


def signed(value, bits=16):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value >> (bits - 1) else value


def fold(value, bits):
    value &= (1 << bits) - 1
    result = value & MASK
    for shift in range(16, bits, 16):
        result = ((result * 33) ^ (value >> shift & MASK)) & MASK
    return result


def operation(name, left, right, *, bits=16, signed_values=False):
    if name == 'add': result = left + right
    elif name == 'sub': result = left - right
    elif name == 'mul': result = left * right
    elif name == 'and': result = left & right
    elif name == 'or': result = left | right
    elif name == 'xor': result = left ^ right
    elif name == 'shl': result = left << right if right < bits else 0
    elif name == 'shr': result = left >> right if right < bits else (-1 if signed_values and left < 0 else 0)
    elif name in ('div', 'rem'):
        quotient = abs(left) // abs(right) * (-1 if (left < 0) != (right < 0) else 1)
        result = quotient if name == 'div' else left - quotient * right
    else: raise ValueError(name)
    return result & ((1 << bits) - 1)


@dataclass
class Case:
    backend: str
    category: str
    seed: int
    sources: dict[str, str]
    expected: int
    manifest: dict | None = None
    expected_rejection: bool = False


def edge(rng):
    return rng.choice(EDGES) if rng.randrange(2) else rng.randrange(65536)


def expression(rng, env, depth, *, c=False, comparisons=True):
    if depth <= 0 or rng.randrange(5) == 0:
        if rng.randrange(3):
            name = rng.choice(tuple(env))
            return name, env[name]
        value = edge(rng)
        return str(value) + ('u' if c else ''), value
    if comparisons and rng.randrange(7) == 0:
        left, a = expression(rng, env, depth - 1, c=c, comparisons=False)
        right, b = expression(rng, env, depth - 1, c=c, comparisons=False)
        name = rng.choice(('==', '!=', '<', '>', '<=', '>='))
        x, y = (a, b) if c else (signed(a), signed(b))
        expected = int({'==': x == y, '!=': x != y, '<': x < y, '>': x > y, '<=': x <= y, '>=': x >= y}[name])
        text = f'({left} {name} {right})'
        return (f'((unsigned){text})' if c else text), expected
    if rng.randrange(6) == 0:
        text, value = expression(rng, env, depth - 1, c=c)
        op = rng.choice(('~', '-'))
        return f'({op}{text})', word(~value if op == '~' else -value)
    name = rng.choice(('add', 'sub', 'mul', 'and', 'or', 'xor', 'shl', 'shr'))
    left, a = expression(rng, env, depth - 1, c=c)
    if name in ('shl', 'shr'):
        b = rng.randrange(16 if c else 21)
        right = str(b) + ('u' if c else '')
    else:
        right, b = expression(rng, env, depth - 1, c=c)
    return f'({left} {SYMBOL[name]} {right})', operation(name, a, b)


def simple_case(index, seed):
    rng = random.Random(seed)
    env = {name: edge(rng) for name in ('x', 'y', 'z')}
    prefix = '\n'.join(f'{name} = {value};' for name, value in env.items()) + '\n'
    mode = index % 7
    if mode == 0:
        text, expected = expression(rng, env, 3 + rng.randrange(2))
        return Case('simple', 'nested-expression', seed, {'program.oc': prefix + f'result = {text};\n'}, expected)
    if mode == 1:
        arguments = [expression(rng, env, 1) for _ in range(4)]
        expected = word(arguments[0][1] * 3 + (arguments[1][1] ^ arguments[2][1]) + arguments[3][1] * 2)
        expected = word(expected ^ env['x'])
        source = 'def mix(a,b,c,d) { return (a * 3) + (b ^ c) + (d << 1); }\n'
        source += prefix + 'result = mix(' + ','.join(item[0] for item in arguments) + ') ^ x;\n'
        return Case('simple', 'four-arg-call', seed, {'program.oc': source}, expected)
    if mode == 2:
        count, factor, bias = rng.randrange(1, 9), rng.randrange(1, 7), edge(rng)
        expected = bias
        for n in range(1, count + 1): expected = word(expected * factor + n)
        source = f'def recurse(n) {{ if(n <= 0) {{ return {bias}; }} return recurse(n - 1) * {factor} + n; }}\nresult = recurse({count});\n'
        return Case('simple', 'recursive-call', seed, {'program.oc': source}, expected)
    if mode == 3:
        count = rng.randrange(2, 10)
        expected = env['x']
        for i in range(count):
            expected = word(expected + env['y'] if i & 1 else expected ^ env['z'])
        source = prefix + f'result = x;\nfor(i=0;i<{count};i=i+1) {{ if((i & 1) == 1) {{ result=result+y; }} else {{ result=result^z; }} }}\n'
        return Case('simple', 'loop-branch', seed, {'program.oc': source}, expected)
    if mode == 4:
        values = [edge(rng) for _ in range(rng.randrange(25, 45))]
        source = '\n'.join(f'v{i}={value};' for i, value in enumerate(values))
        names = (len(values) - 1, 0, len(values) // 2, 17)
        expected = word((values[names[0]] + values[names[1]]) ^ word(values[names[2]] * values[names[3]]))
        source += f'\nresult=(v{names[0]}+v{names[1]}) ^ (v{names[2]}*v{names[3]});\n'
        return Case('simple', 'large-frame', seed, {'program.oc': source}, expected)
    if mode == 5:
        count = rng.randrange(18, 32)
        take = signed(env['x']) > signed(env['y'])
        source = prefix + 'result=z;\nif(x>y) {\n'
        for _ in range(count): source += 'result=result+x;\n'
        source += '} else {\n'
        for _ in range(count): source += 'result=result-y;\n'
        source += '}\n'
        expected = word(env['z'] + count * env['x'] if take else env['z'] - count * env['y'])
        return Case('simple', 'far-branch', seed, {'program.oc': source}, expected)
    text, value = expression(rng, env, 2)
    source = 'def add(a,b) { return a+b; }\ndef twice(a) { return add(a,a); }\n' + prefix
    source += f'result = ({text}) + add(twice(x), add(y,z));\n'
    expected = word(value + word(env['x'] * 2) + word(env['y'] + env['z']))
    return Case('simple', 'live-values-nested-calls', seed, {'program.oc': source}, expected)


def c_literal(value, bits, is_signed):
    suffix = ('' if is_signed else 'u') if bits <= 16 else ('L' if bits == 32 else 'LL') + ('' if is_signed else 'U')
    if is_signed and value == -(1 << (bits - 1)) and bits >= 16:
        return f'(-{(1 << (bits - 1)) - 1}{suffix} - 1{suffix})'
    return f'{value}{suffix}'


def c_integer(index, seed):
    rng = random.Random(seed)
    bits = (8, 16, 32, 64)[index % 4]
    name = OPS[(index // 4) % len(OPS)]
    is_signed = bool(index // (4 * len(OPS)) % 2)
    ctype = ('signed char', 'int', 'long', 'long long')[(8, 16, 32, 64).index(bits)]
    unsigned = ('unsigned char', 'unsigned int', 'unsigned long', 'unsigned long long')[(8, 16, 32, 64).index(bits)]
    if not is_signed: ctype = unsigned
    mask, maximum = (1 << bits) - 1, (1 << (bits - 1)) - 1
    if is_signed:
        a = rng.choice((-(1 << (bits - 1)), -1, 0, 1, maximum, rng.randint(-maximum, maximum)))
        b = rng.choice((-17, -1, 1, 2, 17, maximum))
        if name in ('add', 'sub'):
            a, b = rng.randrange(-(1 << (bits - 2)), 1 << (bits - 2)), rng.randrange(-(1 << (bits - 2)), 1 << (bits - 2))
        elif name == 'mul':
            bound = 1 << (bits // 2 - 1)
            a, b = rng.randrange(-bound, bound), rng.randrange(-bound, bound)
        elif name in ('div', 'rem') and a == -(1 << (bits - 1)) and b == -1: b = 2
    else:
        a = rng.choice((0, 1, mask, mask - 1, 1 << (bits - 1), rng.randrange(mask + 1)))
        b = rng.choice((1, 2, 17, mask, rng.randrange(1, mask + 1)))
    if name in ('shl', 'shr'):
        b = rng.choice([n for n in (0, 1, 7, 15, 16, 17, 31, 32, 33, 47, 48, 63) if n < bits])
        if is_signed and name == 'shl': a = rng.randrange((maximum >> b) + 1)
    expected_word = operation(name, a, b, bits=bits, signed_values=is_signed)
    expected = fold(expected_word, bits)
    expr = f'left {SYMBOL[name]} right'
    if bits == 8 and not is_signed: expr = f'(unsigned int)left {SYMBOL[name]} (unsigned int)right'
    checksum = ''.join(f'checksum = checksum * 33u ^ (unsigned)(value >> {shift});\n' for shift in range(16, bits, 16))
    # Avoid a wrapper plus a second eight-slot call around a heavy 64-bit helper.
    source = f'''#include <stdint.h>
volatile {ctype} a={c_literal(a,bits,is_signed)}, b={c_literal(b,bits,is_signed)};
int main(void) {{
  {ctype} left=a, right=b;
  {ctype} answer=({ctype})({expr});
  {unsigned} value=({unsigned})answer;
  unsigned checksum=(unsigned)value;
  {checksum}
  return (int)checksum;
}}
'''
    return Case('c', f'integer-{bits}-{"signed" if is_signed else "unsigned"}-{name}', seed, {'main.c': source}, expected)


C_MODES = ('integer', 'expression', 'integer', 'control', 'integer', 'calls', 'integer', 'recursion',
           'integer', 'arrays', 'integer', 'memory', 'integer', 'multifile', 'integer', 'globals', 'booleans')


def c_case(index, seed, integer_index):
    mode = C_MODES[index % len(C_MODES)]
    if mode == 'integer': return c_integer(integer_index, seed)
    rng = random.Random(seed)
    x, y, z = edge(rng), edge(rng), edge(rng)
    prefix = f'volatile unsigned ax={x}u, ay={y}u, az={z}u;\n'
    if mode == 'expression':
        text, expected = expression(rng, dict(x=x, y=y, z=z), 3, c=True)
        return Case('c', mode, seed, {'main.c': prefix + f'int main(void){{unsigned x=ax,y=ay,z=az;return (int)({text});}}\n'}, expected)
    if mode == 'control':
        count = rng.randrange(2, 12)
        expected = x
        for i in range(count):
            selector = (i + y) & 3
            expected = word(expected + z if selector == 0 else expected ^ y if selector == 1 else expected * 3 if selector == 2 else expected - x)
        source = prefix + f'''int main(void) {{ unsigned x=ax,y=ay,z=az,result=x;
          for(unsigned i=0;i<{count}u;i++) {{ switch((i+y)&3u) {{
          case 0: result+=z; break; case 1: result^=y; break;
          case 2: result*=3u; break; default: result-=x; }} }} return (int)result; }}'''
        return Case('c', mode, seed, {'main.c': source}, expected)
    if mode == 'calls':
        # A wide parameter begins in a4 and continues on the outgoing stack.
        wide, tail = rng.getrandbits(64), rng.randrange(30)
        expected = fold((wide + x + y + z + tail) & ((1 << 64) - 1), 64) ^ word(x * 7 + 3)
        source = prefix + f'''#include <stdint.h>
volatile uint64_t wide={wide}ULL;
static uint64_t join(unsigned a,unsigned b,unsigned c,uint64_t value,unsigned tail) {{ return value+a+b+c+tail; }}
static unsigned clobber(unsigned x) {{ return x*7u+3u; }}
int main(void) {{ uint64_t value=join(ax,ay,az,wide,{tail}u); unsigned side=clobber(ax);
unsigned sum=(unsigned)value; sum=sum*33u^(unsigned)(value>>16);sum=sum*33u^(unsigned)(value>>32);sum=sum*33u^(unsigned)(value>>48);
return (int)(sum^side); }}'''
        return Case('c', 'wide-call-live-values', seed, {'main.c': source}, word(expected))
    if mode == 'recursion':
        n, multiplier, bias = rng.randrange(2, 10), rng.randrange(2, 8), x
        value = bias
        for i in range(1, n + 1): value = word(value * multiplier + i)
        source = f'''unsigned recurse(unsigned n) {{ if(!n)return {bias}u; return recurse(n-1u)*{multiplier}u+n; }}
int main(void) {{ return (int)recurse({n}u); }}'''
        return Case('c', mode, seed, {'main.c': source}, value)
    if mode == 'arrays':
        count = rng.randrange(40, 100)
        step = rng.randrange(1, 30)
        values = [word(x + i * step) for i in range(count)]
        offset, byte = rng.randrange(count * 2), rng.randrange(256)
        shift = offset % 2 * 8
        values[offset // 2] = (values[offset // 2] & ~(255 << shift)) | byte << shift
        expected = sum(values) & MASK
        source = f'''#include <stdint.h>
int main(void) {{ uint16_t values[{count}]; uint16_t *p=values;
for(unsigned i=0;i<{count}u;i++) p[i]={x}u+i*{step}u;
unsigned char *bytes=(unsigned char*)p; bytes[{offset}]={byte};
unsigned sum=0; for(unsigned i=0;i<{count}u;i++)sum+=*(p+i); return (int)sum; }}'''
        return Case('c', 'large-frame-dynamic-pointer', seed, {'main.c': source}, expected)
    if mode == 'memory':
        which = ('memcpy', 'memmove', 'memset', 'memcmp')[(index // len(C_MODES)) % 4]
        count, size = rng.randrange(8, 20), 28
        values = [(i * 7 + x) & 255 for i in range(size)]
        source = f'''#include <string.h>
int main(void) {{ unsigned char values[{size}];
for(unsigned i=0;i<{size}u;i++) values[i]=(unsigned char)(i*7u+{x}u);
'''
        if which == 'memcpy':
            incoming = [rng.randrange(256) for _ in range(count)]
            start = rng.randrange(0, size - count + 1)
            literal = ','.join(map(str, incoming))
            source = f'#include <string.h>\nunsigned char incoming[{count}]={{{literal}}};\n' + source.replace('#include <string.h>\n', '')
            source += f'memcpy(values+{start},incoming,{count});\n'
            values[start:start + count] = incoming
        elif which == 'memmove':
            src, dst = (0, rng.randrange(1, 6)) if rng.randrange(2) else (rng.randrange(1, 6), 0)
            source += f'memmove(values+{dst},values+{src},{count});\n'
            values[dst:dst + count] = values[src:src + count]
        elif which == 'memset':
            start, value = rng.randrange(0, size - count + 1), rng.randrange(256)
            source += f'memset(values+{start},{value},{count});\n'
            values[start:start + count] = [value] * count
        else:
            relation = (index // (len(C_MODES) * 4)) % 3
            candidates = [i for i, value in enumerate(values)
                          if relation == 0 or relation == 1 and value < 255 or relation == 2 and value > 0]
            difference = rng.choice(candidates)
            altered = values.copy()
            altered[difference] += 0 if relation == 0 else 1 if relation == 1 else -1
            literal = ','.join(map(str, altered))
            source = f'#include <string.h>\nunsigned char comparison[{size}]={{{literal}}};\n' + source.replace('#include <string.h>\n', '')
            source += f'int comparison_result=memcmp(values,comparison,{size});return comparison_result<0?-1:comparison_result>0?1:0;}}\n'
            delta = values[difference] - altered[difference]
            return Case('c', which, seed, {'main.c': source}, MASK if delta < 0 else 1 if delta > 0 else 0)
        source += f'unsigned sum=0;for(unsigned i=0;i<{size}u;i++)sum=sum*33u^values[i];return (int)sum;}}\n'
        expected = 0
        for value in values: expected = word(expected * 33 ^ value)
        return Case('c', which, seed, {'main.c': source}, expected)
    if mode == 'multifile':
        factor, mask, shared, bias = rng.randrange(1, 9), edge(rng), rng.randrange(20), rng.randrange(50)
        first, second = word(x * factor) ^ mask, word(x * 3 + 7)
        expected = word(word(first + y) ^ second)
        expected = word(expected + shared + bias)
        sources = {
            'main.c': f'#include "api.h"\nvolatile unsigned input={x}u; static unsigned local(unsigned x){{return x*3u+7u;}}\nint main(void){{unsigned saved=input;unsigned result=helper(saved,{y}u);return (int)((result^local(saved))+shared+BIAS);}}\n',
            'math.c': f'#include "api.h"\nunsigned shared={shared}u;static unsigned local(unsigned x){{return x*{factor}u^{mask}u;}}\nunsigned helper(unsigned x,unsigned y){{return local(x)+y;}}\n',
            'include/api.h': 'extern unsigned shared; unsigned helper(unsigned,unsigned);\n',
        }
        manifest = dict(version=1, sources=['main.c', 'math.c'], include_dirs=['include'], defines=[f'BIAS={bias}u'])
        return Case('c', mode, seed, sources, expected, manifest)
    if mode == 'globals':
        index, replacement = rng.randrange(7), rng.randrange(256)
        wide = rng.getrandbits(32)
        original = [rng.randrange(256) for _ in range(7)]; original[index] = 42
        # The expected list must use the same non-mutated global bytes.
        expected = word(sum(original) - original[index] + replacement + (wide & MASK) + (wide >> 16))
        source = f'''#include <stdint.h>
unsigned char bytes[7]={{{','.join(map(str,original))}}}; unsigned char *selected=bytes+{index};
uint32_t number={wide}UL;
int main(void) {{ *selected={replacement};unsigned sum=0;for(unsigned i=0;i<7u;i++)sum+=bytes[i];
return (int)(sum+(unsigned)number+(unsigned)(number>>16)); }}'''
        return Case('c', mode, seed, {'main.c': source}, expected)
    expected = int(x < y) * 101 + int(x == y) * 7 + int(z != 0) * 23
    source = prefix + '''#include <stdbool.h>
int main(void) { unsigned x=ax,y=ay,z=az;bool values[3];values[0]=x<y;values[1]=x==y;values[2]=!!z;
return values[0]*101+values[1]*7+values[2]*23; }'''
    return Case('c', 'boolean-memory', seed, {'main.c': source}, expected)


def persist(case, directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name, source in case.sources.items():
        path = directory / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(source)
    if case.manifest is not None:
        (directory / 'case.opencpu.json').write_text(json.dumps(case.manifest, indent=2))
    (directory / 'case.json').write_text(json.dumps(asdict(case), indent=2))
    (directory / 'expected.json').write_text(json.dumps({'result': case.expected}, indent=2))


def compile_case(case, directory):
    toolchain = Toolchain()
    if case.manifest is not None:
        return toolchain.compile_project(CProject.load(directory / 'case.opencpu.json'))
    path = directory / ('program.oc' if case.backend == 'simple' else 'main.c')
    return toolchain.compile(path.read_text(), backend='simple' if case.backend == 'simple' else 'llvm',
                             language='auto' if case.backend == 'simple' else 'c', source_name=str(path))


def execute_case(case, directory):
    started = time.monotonic()
    build = compile_case(case, directory)
    (directory / 'program.asm').write_text(build.assembly)
    (directory / 'program.bin').write_text(build.binary)
    model = Simulator(build.entry_pc, history_limit=0)
    model.inst_mem = build.words
    model.run(max_steps=250000)
    if model.faulted or not model.halted:
        raise AssertionError(f'program did not HALT: {model.stop_reason}, {model.fault_reason}')
    actual = (model.peek_data(1022 + build.variable_offsets['result']) if case.backend == 'simple' else model.registers[1])
    if actual != case.expected:
        raise AssertionError(f'independent result mismatch: expected {case.expected}, actual {actual}')
    if model.registers[0] != 0:
        raise AssertionError('zero register changed')
    if case.backend == 'c' and (model.registers[5] != 0 or model.registers[7] != 1024):
        raise AssertionError(f'C ABI not restored: FP={model.registers[5]}, SP={model.registers[7]}')
    result = dict(status='passed', backend=case.backend, category=case.category, seed=case.seed,
                  expected=case.expected, actual=actual, words=len(build.words), retired=model.instructions_retired,
                  duration_seconds=round(time.monotonic() - started, 6))
    (directory / 'result.json').write_text(json.dumps(result, indent=2))
    return result, build


class _UARTAcceptance(SocDriverMixin, unittest.TestCase):
    def run_image(self, words, **options):
        state, records = super().run_image(words, **options)
        (self.artifact_directory / 'retirement.jsonl').write_text(
            ''.join(json.dumps(record) + '\n' for record in records))
        (self.artifact_directory / 'rtl.json').write_text(json.dumps(state, indent=2))
        return state, records


def rtl_case(case, build, directory):
    checker = _UARTAcceptance()
    checker.artifact_directory = directory
    checker.setUpClass()
    # SocDriverMixin runs the actual board top, uploads pin-level UART bytes,
    # and compares every retirement and final RAM to a fresh software model.
    state = checker.assert_matches_reference(build, max_cycles=750000)
    actual = (checker.memory(state, 1022 + build.variable_offsets['result']) if case.backend == 'simple' else state['registers'][1])
    if actual != case.expected:
        raise AssertionError(f'RTL independent result mismatch: expected {case.expected}, actual {actual}')
    (directory / 'rtl.json').write_text(json.dumps(state, indent=2))


def select_rtl(successes, count, rng):
    if count > len(successes):
        raise ValueError(f'need {count} RTL samples but only {len(successes)} compilations passed')
    groups = {}
    for item in successes:
        category = item[0].category
        family = '-'.join(category.split('-')[:3]) if category.startswith('integer-') else category
        groups.setdefault(family, []).append(item)
    for items in groups.values(): rng.shuffle(items)
    selected = []
    while len(selected) < count:
        for name in sorted(groups):
            if groups[name] and len(selected) < count:
                selected.append(groups[name].pop())
    return selected


def rejection_cases(seed):
    for depth in (1000, 2000):
        yield Case('simple', f'resource-expression-{depth}', seed,
                   {'program.oc': 'result=' + '+'.join(['1'] * depth) + ';'}, 0, expected_rejection=True)
    yield Case('simple', 'resource-locals', seed,
               {'program.oc': '\n'.join(f'v{i}=1;' for i in range(1001))}, 0, expected_rejection=True)
    yield Case('simple', 'resource-ROM', seed,
               {'program.oc': 'result=' + '+'.join(['1'] * 300) + ';'}, 0, expected_rejection=True)
    yield Case('c', 'resource-static-RAM', seed,
               {'main.c': 'volatile unsigned char data[2048];int main(void){return data[0];}'}, 0, expected_rejection=True)
    yield Case('c', 'resource-ROM', seed,
               {'main.c': 'int main(void){volatile unsigned value=0;' + 'value+=1u;' * 1000 + 'return (int)value;}'}, 0,
               expected_rejection=True)


def check_rejection(case, directory, summary, categories):
    persist(case, directory)
    try:
        build = compile_case(case, directory)
    except ValueError as error:
        if not RESOURCE.search(str(error)):
            raise AssertionError('expected a controlled capacity/nesting diagnostic: ' + str(error)) from error
        (directory / 'rejection.txt').write_text(str(error) + '\n')
        summary['resource_rejections'].append(dict(backend=case.backend, category=case.category,
            seed=case.seed, path=str(directory), diagnostic=str(error), expected=True))
        categories[f'{case.backend}:{case.category}:resource_rejected'] += 1
    else:
        (directory / 'program.asm').write_text(build.assembly)
        (directory / 'program.bin').write_text(build.binary)
        raise AssertionError('over-capacity program unexpectedly compiled')


def positive(value):
    parsed = int(value, 0)
    if parsed < 0: raise argparse.ArgumentTypeError('must be nonnegative')
    return parsed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=positive, default=20261030)
    parser.add_argument('--cases', type=positive, help='override both per-compiler counts')
    parser.add_argument('--simple-cases', type=positive)
    parser.add_argument('--c-cases', type=positive)
    parser.add_argument('--rtl-cases', type=positive, default=50, help='UART samples per compiler; zero disables RTL explicitly')
    parser.add_argument('--output', type=Path, default=REPOSITORY / 'build/stress/latest/compilers')
    parser.add_argument('--replay', type=Path, help='case directory or case.json to replay')
    args = parser.parse_args(argv)
    simple_count = args.simple_cases if args.simple_cases is not None else args.cases if args.cases is not None else 300
    c_count = args.c_cases if args.c_cases is not None else args.cases if args.cases is not None else 250
    output = args.output.expanduser().resolve(); output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    summary = dict(seed=args.seed, passed=0, failed=0, duration_seconds=0, categories={}, resource_rejections=[],
                   simple=dict(requested=simple_count, passed=0, failed=0, generated=0, rtl_passed=0, rtl_failed=0),
                   c=dict(requested=c_count, passed=0, failed=0, generated=0, rtl_passed=0, rtl_failed=0),
                   failures=[], rtl_requested_per_backend=args.rtl_cases)
    successes = {'simple': [], 'c': []}
    categories = Counter(); integer_index = 0
    master = random.Random(args.seed)
    replay = None
    if args.replay:
        path = args.replay / 'case.json' if args.replay.is_dir() else args.replay
        replay = Case(**json.loads(path.read_text()))
        for backend in successes:
            summary[backend]['requested'] = int(replay.backend == backend and not replay.expected_rejection)
    try:
        for backend, requested in (('simple', simple_count), ('c', c_count)):
            if replay is not None and replay.backend != backend: continue
            if replay is not None:
                requested = 0 if replay.expected_rejection else 1
                summary[backend]['requested'] = requested
            index = 0
            while summary[backend]['passed'] + summary[backend]['failed'] < requested and index < max(1, requested * 2):
                seed = master.getrandbits(64)
                case = replay or (simple_case(index, seed) if backend == 'simple' else c_case(index, seed, integer_index))
                if backend == 'c' and C_MODES[index % len(C_MODES)] == 'integer': integer_index += 1
                directory = output / backend / f'{index:05d}-{case.category}'
                persist(case, directory)
                summary[backend]['generated'] += 1
                try:
                    result, build = execute_case(case, directory)
                except Exception as error:
                    diagnostic = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
                    (directory / 'failure.txt').write_text(diagnostic)
                    if isinstance(error, ValueError) and RESOURCE.search(str(error)):
                        summary['resource_rejections'].append(dict(backend=backend, category=case.category, seed=case.seed,
                                                                   path=str(directory), diagnostic=str(error)))
                        categories[f'{backend}:{case.category}:resource_rejected'] += 1
                    else:
                        summary['failed'] += 1; summary[backend]['failed'] += 1
                        failure = dict(backend=backend, category=case.category, seed=case.seed,
                                       path=str(directory), diagnostic=str(error))
                        summary['failures'].append(failure)
                        categories[f'{backend}:{case.category}:failed'] += 1
                        print(json.dumps(dict(event='failure', **failure)), flush=True)
                else:
                    summary['passed'] += 1; summary[backend]['passed'] += 1
                    categories[f'{backend}:{case.category}:passed'] += 1
                    successes[backend].append((case, build, directory))
                index += 1
                if index % 25 == 0:
                    print(json.dumps(dict(event='progress', backend=backend, **summary[backend])), flush=True)
                if replay is not None: break
            if summary[backend]['passed'] + summary[backend]['failed'] < requested:
                raise AssertionError(f'{backend}: too many resource rejections to achieve requested functional count')
        resources = ([replay] if replay is not None and replay.expected_rejection else
                     [] if replay is not None else
                     [case for case in rejection_cases(args.seed) if summary[case.backend]['requested']])
        for case in resources:
            directory = output / 'resource-rejections' / f'{case.backend}-{case.category}'
            try:
                check_rejection(case, directory, summary, categories)
            except Exception as error:
                summary['failed'] += 1
                summary['failures'].append(dict(backend=case.backend, category=case.category,
                    path=str(directory), seed=case.seed, diagnostic=str(error), phase='expected-resource-rejection'))
                (directory / 'failure.txt').write_text(traceback.format_exc())
        if args.rtl_cases:
            for backend, items in successes.items():
                if not items: continue
                selected = select_rtl(items, min(args.rtl_cases, len(items)) if replay is not None else args.rtl_cases, master)
                for case, build, directory in selected:
                    try: rtl_case(case, build, directory)
                    except Exception as error:
                        summary['failed'] += 1; summary[backend]['rtl_failed'] += 1
                        failure = dict(backend=backend, category=case.category, seed=case.seed,
                                       path=str(directory), diagnostic=str(error), phase='rtl')
                        summary['failures'].append(failure)
                        (directory / 'rtl-failure.txt').write_text(traceback.format_exc())
                        print(json.dumps(dict(event='failure', **failure)), flush=True)
                    else:
                        summary[backend]['rtl_passed'] += 1
        # A whole feature category being rejected for capacity is not coverage.
        for key in list(categories):
            if key.endswith(':resource_rejected') and ':resource-' not in key:
                prefix = key.rsplit(':', 1)[0]
                if not categories[prefix + ':passed']:
                    raise AssertionError(f'no successful functional coverage for {prefix}')
    except Exception as error:
        summary['failed'] += 1
        summary['failures'].append(dict(phase='runner', diagnostic=str(error)))
        print(traceback.format_exc(), file=sys.stderr)
    summary['categories'] = dict(sorted(categories.items()))
    summary['duration_seconds'] = round(time.monotonic() - started, 6)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), flush=True)
    return int(bool(summary['failed']))


if __name__ == '__main__':
    raise SystemExit(main())
