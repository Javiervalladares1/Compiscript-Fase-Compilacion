"""Traduccion TAC -> MIPS32 para SPIM y MARS.

Cada activacion tiene sus propios parametros, locales y temporales. Los
primeros cuatro argumentos usan $a0-$a3 (float como bits de una palabra);
los restantes usan el area de argumentos del caller. Los floats se calculan
con COP1 y retornan en $f0; los otros valores retornan en $v0.
"""

from __future__ import annotations

import struct

from ..ir.generator import CodegenError
from ..ir.model import Constant, Instruction, IRFunction, IRProgram, Operand, Place
from ..types.types import BOOLEAN, FLOAT, INTEGER, NULL, STRING
from .registers import RegisterAllocator
from .runtime import RUNTIME_DATA, RUNTIME_TEXT


def align8(size: int) -> int:
    return (size + 7) // 8 * 8


class MIPSGenerator:
    def __init__(self, allocation: str = "registers"):
        if allocation not in ("registers", "stack"):
            raise ValueError("allocation debe ser 'registers' o 'stack'")
        self.allocation = allocation
        self.strings: dict[str, str] = {}
        self.lines: list[str] = []
        self.label_id = 0

    def emit(self, line: str) -> None:
        self.lines.append("    " + line)

    def branch(self, text: str) -> None:
        self.emit(text)
        self.emit("nop")

    def label(self) -> str:
        self.label_id += 1
        return f"_cs_B{self.label_id}"

    def string_label(self, value: str) -> str:
        if value not in self.strings:
            self.strings[value] = f"_cs_str{len(self.strings)}"
        return self.strings[value]

    def address(self, place: Place) -> str:
        if place.storage == "global":
            return place.name
        if place.owner and place.owner != self.current_function.name:
            self.frame_address(place.owner, "$t9")
            return f"{self.layouts[place.owner][place]}($t9)"
        return f"{self.offsets[place]}($fp)"

    def frame_address(self, owner: str, register: str) -> None:
        function = self.current_function
        self.emit(f"move {register}, $fp")
        while function.name != owner:
            if function.static_link is None or function.parent is None:
                raise CodegenError("La captura no pertenece a un ancestro lexico de la funcion.")
            offset = self.layouts[function.name][function.static_link]
            self.emit(f"lw {register}, {offset}({register})")
            function = self.functions[function.parent]

    def load(self, register: str, value: Operand) -> None:
        if isinstance(value, Place):
            self.emit(f"lw {register}, {self.address(value)}")
        elif value.type == STRING:
            self.emit(f"la {register}, {self.string_label(str(value.value))}")
        elif value.type == FLOAT:
            bits = struct.unpack("!I", struct.pack("!f", float(value.value)))[0]
            self.emit(f"li {register}, 0x{bits:08x}")
        else:
            self.emit(f"li {register}, {int(value.value or 0)}")

    def store(self, register: str, place: Place) -> None:
        self.emit(f"sw {register}, {self.address(place)}")

    def generate(self, program: IRProgram) -> str:
        self.functions = {function.name: function for function in program.functions}
        self.layouts = {}
        self.local_sizes = {}
        for function in program.functions:
            offsets, size = {}, 0
            for place in function.places:
                offsets[place] = size
                size += 56 if place.storage == "handler" else 4
            self.layouts[function.name] = offsets
            self.local_sizes[function.name] = size
        functions = [self.function(function) for function in program.functions]
        data = ["# Generado por Compiscript - MIPS32 (SPIM/MARS)", ".data", RUNTIME_DATA.strip()]
        for place in program.globals:
            data.extend([".align 2", f"{place.name}: .word 0"])
        for name, methods in program.vtables.items():
            data.extend([".align 2", f"_cs_vt_{name}: .word " + ", ".join(methods or ["0"])])
        for value, label in self.strings.items():
            data.append(f"{label}:")
            encoded = list(value.encode("utf-8")) + [0]
            for start in range(0, len(encoded), 24):
                data.append("    .byte " + ", ".join(map(str, encoded[start:start + 24])))
        entry = '''
.text
.globl main
main:
    # SPIM puede entregar $sp con alineacion de 4; ABI interna usa 8.
    li $t9, -8
    and $sp, $sp, $t9
    jal _cs_entry
    nop
    li $v0, 10
    syscall
'''
        return "\n".join(data) + "\n" + entry + "\n".join(functions) + RUNTIME_TEXT

    def function(self, function: IRFunction) -> str:
        self.lines = []
        self.current_function = function
        self.offsets = self.layouts[function.name]
        self.allocator = RegisterAllocator(function, self.emit, self.load, self.store)
        self.epilogue = f"{function.name}_return"
        for position, instruction in enumerate(function.instructions):
            self.allocator.position = position
            self.emit("# " + str(instruction).replace("\n", " | "))
            self.instruction(instruction)
            if self.allocation == "stack":
                self.allocator.flush()
        self.allocator.flush()
        body = self.lines
        saved = sorted(self.allocator.used_saved)
        frame_size = align8(self.local_sizes[function.name] + 8 + 4 * len(saved))
        if frame_size > 32760 or len(function.parameters) * 4 + frame_size > 32760:
            raise CodegenError("El marco de la funcion excede los desplazamientos de 16 bits de MIPS.")
        self.lines = ["", f"{function.name}:"]
        self.emit(f"# frame={frame_size} bytes; modo={self.allocation}; spills={self.allocator.spills}")
        self.emit(f"addiu $sp, $sp, -{frame_size}")
        self.emit(f"sw $ra, {frame_size - 4}($sp)")
        self.emit(f"sw $fp, {frame_size - 8}($sp)")
        for index, register in enumerate(saved):
            self.emit(f"sw {register}, {frame_size - 12 - 4 * index}($sp)")
        self.emit("move $fp, $sp")
        for index, parameter in enumerate(function.parameters):
            if index < 4:
                register = f"$a{index}"
            else:
                register = "$t8"
                self.emit(f"lw $t8, {frame_size + 4 * index}($fp)")
            self.store(register, parameter)
        self.lines.extend(body)
        self.lines.append(self.epilogue + ":")
        self.emit("move $sp, $fp")
        for index, register in enumerate(saved):
            self.emit(f"lw {register}, {frame_size - 12 - 4 * index}($sp)")
        self.emit(f"lw $ra, {frame_size - 4}($sp)")
        self.emit(f"lw $fp, {frame_size - 8}($sp)")
        self.emit(f"addiu $sp, $sp, {frame_size}")
        self.branch("jr $ra")
        return "\n".join(self.lines) + "\n"

    def call(self, target: str, args: tuple[Operand, ...], result: Place | None,
             *, virtual: bool = False) -> None:
        self.allocator.flush()
        area = align8(max(16, 4 * len(args)))
        if area > 32760:
            raise CodegenError("Demasiados argumentos para la llamada MIPS.")
        self.emit(f"addiu $sp, $sp, -{area}")
        for index, arg in enumerate(args):
            register = f"$a{index}" if index < 4 else "$t8"
            self.load(register, arg)
            if index >= 4:
                self.emit(f"sw {register}, {4 * index}($sp)")
        if virtual:
            self.branch("beq $a0, $zero, _cs_nullref")
            self.emit("lw $t9, 0($a0)")
            self.emit(f"lw $t9, {target}($t9)")
            self.branch("jalr $t9")
        else:
            self.branch(f"jal {target}")
        self.emit(f"addiu $sp, $sp, {area}")
        if result is not None:
            register = self.allocator.getReg(result, write=True)
            if result.type == FLOAT:
                self.emit(f"mfc1 {register}, $f0")
            else:
                self.emit(f"move {register}, $v0")

    def instruction(self, instruction: Instruction) -> None:
        op, args, dest = instruction.op, instruction.args, instruction.result
        allocator = self.allocator
        if op == "try_push":
            allocator.flush()
            self.emit(f"addiu $t8, $fp, {self.offsets[args[0]]}")
            self.emit("lw $t9, _cs_handler")
            self.emit("sw $t9, 0($t8)")
            self.emit(f"la $t9, {instruction.target}")
            self.emit("sw $t9, 4($t8)")
            for offset, register in enumerate(("$sp", "$fp", "$ra", *(f"$s{i}" for i in range(8))), start=2):
                self.emit(f"sw {register}, {4 * offset}($t8)")
            self.emit("sw $t8, _cs_handler")
            return
        if op == "try_pop":
            allocator.flush()
            self.emit("lw $t8, _cs_handler")
            self.emit("lw $t9, 0($t8)")
            self.emit("sw $t9, _cs_handler")
            return
        # Un salto al catch descarta los registros del camino fallido. Hacer
        # visibles en memoria todos los efectos anteriores al posible error.
        if op in ("/", "%", "length", "load_index", "store_index", "load_field", "store_field"):
            allocator.flush()
        if op in ("label", "jump", "ifz", "return"):
            register = allocator.getReg(args[0]) if args else None
            allocator.flush()
            if op == "label":
                self.lines.append(instruction.target + ":")
            elif op == "jump":
                self.branch(f"b {instruction.target}")
            elif op == "ifz":
                self.branch(f"beq {register}, $zero, {instruction.target}")
            else:
                if register is not None:
                    if args[0].type == FLOAT:
                        self.emit(f"mtc1 {register}, $f0")
                    else:
                        self.emit(f"move $v0, {register}")
                self.branch(f"b {self.epilogue}")
            return
        if op in ("call", "vcall"):
            self.call(instruction.target, args, dest, virtual=op == "vcall")
            return
        if op == "concat":
            self.call("_cs_concat", args, dest)
            return
        if op in ("==", "!=") and args[0].type == args[1].type == STRING:
            self.call("_cs_streq", args, dest)
            if op == "!=":
                register = allocator.getReg(dest, write=True)
                self.emit(f"xori {register}, {register}, 1")
            return
        if op == "to_string" and args[0].type == INTEGER:
            self.call("_cs_itoa", args, dest)
            return
        if op == "print":
            self.print_value(args[0])
            return
        registers: list[str] = []
        for arg in args:
            registers.append(allocator.getReg(arg, pinned=tuple(registers)))
        result = allocator.getReg(dest, write=True, pinned=tuple(registers)) if dest else None
        left = registers[0] if registers else ""
        right = registers[1] if len(registers) > 1 else ""
        if op == "copy":
            self.emit(f"move {result}, {left}")
        elif op == "frame_ref":
            self.frame_address(instruction.target, result)
        elif op == "catch":
            self.emit(f"move {result}, $v1")
        elif op == "int_to_float":
            self.emit(f"mtc1 {left}, $f2")
            self.emit("cvt.s.w $f4, $f2")
            self.emit(f"mfc1 {result}, $f4")
        elif op == "to_string":
            if args[0].type == NULL:
                self.emit(f"la {result}, _cs_null")
            else:
                self.boolean_string(left, result)
        elif op == "!":
            self.emit(f"sltiu {result}, {left}, 1")
        elif op == "neg":
            if args[0].type == FLOAT:
                self.emit(f"mtc1 {left}, $f2")
                self.emit("neg.s $f4, $f2")
                self.emit(f"mfc1 {result}, $f4")
            else:
                self.emit(f"subu {result}, $zero, {left}")
        elif op == "new_array":
            self.emit(f"sll $a0, {left}, 2")
            self.emit("addiu $a0, $a0, 4")
            self.emit("li $v0, 9")
            self.emit("syscall")
            self.emit(f"move {result}, $v0")
            self.emit(f"sw {left}, 0({result})")
        elif op == "new_object":
            self.emit(f"move $a0, {left}")
            self.emit("li $v0, 9")
            self.emit("syscall")
            self.emit(f"move {result}, $v0")
            self.emit(f"la $t8, _cs_vt_{instruction.target}")
            self.emit(f"sw $t8, 0({result})")
            for offset in range(4, int(args[0].value), 4):
                self.emit(f"sw $zero, {offset}({result})")
        elif op in ("load_field", "store_field"):
            self.branch(f"beq {left}, $zero, _cs_nullref")
            offset = int(args[1].value)
            if op == "load_field":
                self.emit(f"lw {result}, {offset}({left})")
            else:
                self.emit(f"sw {registers[2]}, {offset}({left})")
        elif op == "length":
            self.branch(f"beq {left}, $zero, _cs_bounds")
            self.emit(f"lw {result}, 0({left})")
        elif op in ("load_index", "store_index"):
            self.branch(f"beq {left}, $zero, _cs_bounds")
            self.branch(f"bltz {right}, _cs_bounds")
            self.emit(f"lw $t8, 0({left})")
            self.emit(f"slt $t9, {right}, $t8")
            self.branch("beq $t9, $zero, _cs_bounds")
            self.emit(f"sll $t8, {right}, 2")
            self.emit(f"addu $t8, $t8, {left}")
            if op == "load_index":
                self.emit(f"lw {result}, 4($t8)")
            else:
                self.emit(f"sw {registers[2]}, 4($t8)")
        elif args[0].type == FLOAT:
            self.float_binary(op, result, left, right)
        else:
            self.integer_binary(op, result, left, right)

    def boolean_string(self, value: str, result: str) -> None:
        end = self.label()
        self.emit(f"la {result}, _cs_false")
        self.branch(f"beq {value}, $zero, {end}")
        self.emit(f"la {result}, _cs_true")
        self.lines.append(end + ":")

    def print_value(self, value: Operand) -> None:
        self.allocator.flush()
        self.load("$a0", value)
        if value.type == FLOAT:
            self.emit("mtc1 $a0, $f12")
            service = 2
        elif value.type == BOOLEAN:
            self.emit("move $t8, $a0")
            self.boolean_string("$t8", "$a0")
            service = 4
        elif value.type == STRING:
            ready = self.label()
            self.branch(f"bne $a0, $zero, {ready}")
            self.emit("la $a0, _cs_null")
            self.lines.append(ready + ":")
            service = 4
        elif value.type == NULL:
            self.emit("la $a0, _cs_null")
            service = 4
        else:
            service = 1
        self.emit(f"li $v0, {service}")
        self.emit("syscall")
        self.emit("la $a0, _cs_newline")
        self.emit("li $v0, 4")
        self.emit("syscall")

    def integer_binary(self, op: str, result: str, left: str, right: str) -> None:
        if op in ("+", "-"):
            self.emit(f"{'addu' if op == '+' else 'subu'} {result}, {left}, {right}")
        elif op == "*":
            self.emit(f"mult {left}, {right}")
            self.emit(f"mflo {result}")
        elif op in ("/", "%"):
            self.branch(f"beq {right}, $zero, _cs_divzero")
            normal, done = self.label(), self.label()
            # INT_MIN / -1 no cabe en signed32; conservar semantica modular
            # sin depender del resultado indefinido de div en el simulador.
            self.emit("li $t8, -2147483648")
            self.branch(f"bne {left}, $t8, {normal}")
            self.emit("li $t9, -1")
            self.branch(f"bne {right}, $t9, {normal}")
            self.emit(f"li {result}, {-2147483648 if op == '/' else 0}")
            self.branch(f"b {done}")
            self.lines.append(normal + ":")
            self.emit(f"div $zero, {left}, {right}")
            self.emit(f"{'mflo' if op == '/' else 'mfhi'} {result}")
            self.lines.append(done + ":")
        elif op in ("==", "!="):
            self.emit(f"xor {result}, {left}, {right}")
            if op == "==":
                self.emit(f"sltiu {result}, {result}, 1")
            else:
                self.emit(f"sltu {result}, $zero, {result}")
        elif op in ("<", ">", "<=", ">="):
            a, b = (right, left) if op in (">", "<=") else (left, right)
            self.emit(f"slt {result}, {a}, {b}")
            if op in ("<=", ">="):
                self.emit(f"xori {result}, {result}, 1")
        else:
            raise CodegenError(f"Operacion TAC no soportada: {op}")

    def float_binary(self, op: str, result: str, left: str, right: str) -> None:
        self.emit(f"mtc1 {left}, $f2")
        self.emit(f"mtc1 {right}, $f4")
        if op in ("+", "-", "*", "/"):
            if op == "/":
                self.emit("mtc1 $zero, $f6")
                self.emit("c.eq.s $f4, $f6")
                self.branch("bc1t _cs_divzero")
            mnemonic = {"+": "add", "-": "sub", "*": "mul", "/": "div"}[op]
            self.emit(f"{mnemonic}.s $f6, $f2, $f4")
            self.emit(f"mfc1 {result}, $f6")
        else:
            a, b = ("$f4", "$f2") if op in (">", ">=") else ("$f2", "$f4")
            mnemonic = "eq" if op in ("==", "!=") else "le" if op in ("<=", ">=") else "lt"
            self.emit(f"c.{mnemonic}.s {a}, {b}")
            end = self.label()
            self.emit(f"li {result}, 0")
            self.branch(f"{'bc1t' if op == '!=' else 'bc1f'} {end}")
            self.emit(f"li {result}, 1")
            self.lines.append(end + ":")


def generate_mips(program: IRProgram, allocation: str = "registers") -> str:
    return MIPSGenerator(allocation).generate(program)
