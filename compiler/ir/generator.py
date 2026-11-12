"""Baja el AST semantico a TAC, conservando tipos y orden de evaluacion."""

from __future__ import annotations

import math

from ..ast import nodes as N
from ..symbols.symbols import FunctionSymbol, VariableSymbol
from ..symbols.table import SymbolTable
from ..types.types import BOOLEAN, FLOAT, INTEGER, NULL, STRING, VOID, ArrayType, ClassType, Type
from .model import Constant, Instruction, IRFunction, IRProgram, Operand, Place


class CodegenError(Exception):
    def __init__(self, message: str, span: N.SourceSpan | None = None):
        super().__init__(message)
        self.span = span


class IRGenerator:
    def __init__(self, table: SymbolTable):
        self.table = table
        self.program = IRProgram()
        self.function = IRFunction("_cs_entry")
        self.program.functions.append(self.function)
        self.symbol_places: dict[int, Place] = {}
        self.declarations: dict[int, VariableSymbol | FunctionSymbol] = {}
        self.function_names: dict[int, str] = {}
        self.callables: dict[int, IRFunction] = {}
        self.scope_functions: dict[int, IRFunction] = {}
        self.receivers: dict[str, Place] = {}
        self.field_offsets: dict[int, int] = {}
        self.class_fields: dict[str, list[VariableSymbol]] = {}
        self.initializers: dict[str, IRFunction] = {}
        self.method_slots: dict[str, int] = {}
        self.temp_id = 0
        self.label_id = 0
        self.breaks: list[tuple[str, int]] = []
        self.continues: list[tuple[str, int]] = []
        self.handlers: list[Place] = []
        for scope in table.all_scopes:
            for symbol in scope.symbols.values():
                if symbol.ast_node is not None:
                    self.declarations[id(symbol.ast_node)] = symbol
                if isinstance(symbol, FunctionSymbol):
                    self.function_names[id(symbol)] = f"_cs_fn_{scope.id}_{symbol.name}"
                    function = IRFunction(self.function_names[id(symbol)], symbol.return_type)
                    self.callables[id(symbol)] = function
                    assert symbol.body_scope is not None
                    self.scope_functions[symbol.body_scope.id] = function
        for scope in table.all_scopes:
            for symbol in scope.symbols.values():
                if not isinstance(symbol, FunctionSymbol):
                    continue
                function = self.callables[id(symbol)]
                enclosing = scope.enclosing_function_scope()
                if enclosing is not None:
                    function.parent = self.scope_functions[enclosing.id].name
                    function.static_link = Place("_link_" + function.name, INTEGER, "local", function.name)
                    function.places.append(function.static_link)
                    function.parameters.append(function.static_link)
                if symbol.owner_class:
                    receiver = Place("_this_" + function.name, ClassType(symbol.owner_class), "local", function.name)
                    self.receivers[function.name] = receiver
                    function.places.append(receiver)
                    function.parameters.append(receiver)
        for cls in table.classes:
            for name in cls.methods:
                if name not in self.method_slots:
                    self.method_slots[name] = len(self.method_slots) * 4
        for cls in table.classes:
            fields = []
            for name in reversed(table.classes.ancestors(cls.name)):
                ancestor = table.classes.get(name)
                assert ancestor is not None
                fields.extend(ancestor.fields.values())
            self.class_fields[cls.name] = fields
            for index, field in enumerate(fields):
                self.field_offsets[id(field)] = 4 + index * 4
            self.program.vtables[cls.name] = [
                self.function_names[id(method)] if (method := table.classes.lookup_method(cls.name, name)) else "0"
                for name in self.method_slots
            ]
            function = IRFunction("_cs_init_" + cls.name)
            receiver = Place("_this_" + function.name, ClassType(cls.name), "local", function.name)
            function.parameters.append(receiver)
            function.places.append(receiver)
            self.receivers[function.name] = receiver
            self.initializers[cls.name] = function

    def emit(self, op: str, result: Place | None = None, *args: Operand,
             target: str = "", span: N.SourceSpan | None = None) -> None:
        self.function.instructions.append(Instruction(op, result, tuple(args), target, span))

    def temp(self, type_: Type) -> Place:
        self.temp_id += 1
        place = Place(f"_t{self.temp_id}", type_, owner=self.function.name)
        self.function.places.append(place)
        return place

    def label(self) -> str:
        self.label_id += 1
        return f"_cs_L{self.label_id}"

    def variable(self, symbol: VariableSymbol) -> Place:
        if id(symbol) not in self.symbol_places:
            scope = symbol.scope
            assert scope is not None
            owner = scope.enclosing_function_scope()
            storage = "global" if owner is None else "local"
            function = self.scope_functions[owner.id] if owner is not None else None
            place = Place(f"_v{scope.id}_{symbol.name}", symbol.type, storage, function.name if function else "")
            self.symbol_places[id(symbol)] = place
            if storage == "global":
                self.program.globals.append(place)
            else:
                assert function is not None
                function.places.append(place)
        return self.symbol_places[id(symbol)]

    def receiver(self, span: N.SourceSpan) -> Place:
        function = self.function
        while function.name not in self.receivers and function.parent is not None:
            function = next(f for f in self.callables.values() if f.name == function.parent)
        if function.name not in self.receivers:
            raise CodegenError("No hay un receptor this en este contexto.", span)
        return self.receivers[function.name]

    def unwind(self, depth: int) -> None:
        for _ in self.handlers[depth:]:
            self.emit("try_pop")

    def convert(self, value: Operand, type_: Type, span: N.SourceSpan) -> Operand:
        if value.type == INTEGER and type_ == FLOAT:
            result = self.temp(FLOAT)
            self.emit("int_to_float", result, value, span=span)
            return result
        return value

    def generate(self, ast: N.Program) -> IRProgram:
        # Reservar hogares antes de generar capturas o cuerpos que los usen.
        for scope in self.table.all_scopes:
            for symbol in scope.symbols.values():
                if isinstance(symbol, VariableSymbol) and symbol.owner_class is None:
                    self.variable(symbol)
        for statement in ast.statements:
            self.statement(statement)
        self.emit("return")
        for scope in self.table.all_scopes:
            for symbol in scope.symbols.values():
                if isinstance(symbol, FunctionSymbol):
                    self.lower_function(symbol)
        for cls in self.table.classes:
            self.function = self.initializers[cls.name]
            self.program.functions.append(self.function)
            for field in self.class_fields[cls.name]:
                node = field.ast_node
                if node.initializer is not None:
                    value = self.convert(self.expression(node.initializer), field.type, node.span)
                    self.emit("store_field", None, self.receiver(node.span),
                              Constant(self.field_offsets[id(field)], INTEGER), value, span=node.span)
            self.emit("return")
        return self.program

    def lower_function(self, symbol: FunctionSymbol) -> None:
        node = symbol.ast_node
        self.function = self.callables[id(symbol)]
        self.program.functions.append(self.function)
        assert symbol.body_scope is not None
        for parameter in symbol.parameters:
            param_symbol = symbol.body_scope.symbols[parameter.name]
            assert isinstance(param_symbol, VariableSymbol)
            self.function.parameters.append(self.variable(param_symbol))
        if node.body:
            self.statement(node.body)
        # El frontend ya verifica los retornos faltantes; este retorno cubre void.
        self.emit("return")

    def statement(self, node: N.Statement) -> None:
        if isinstance(node, N.Block):
            for child in node.statements:
                self.statement(child)
        elif isinstance(node, N.VarDecl):
            symbol = self.declarations[id(node)]
            assert isinstance(symbol, VariableSymbol)
            dest = self.variable(symbol)
            if node.initializer is not None:
                value = self.convert(self.expression(node.initializer), dest.type, node.span)
                self.emit("copy", dest, value, span=node.span)
        elif isinstance(node, (N.AssignStmt, N.AssignExpr)):
            self.assignment(node.target, node.value, node.span)
        elif isinstance(node, N.ExpressionStmt):
            self.expression(node.expression)
        elif isinstance(node, N.PrintStmt):
            value = self.expression(node.value)
            if isinstance(value.type, (ArrayType, ClassType)):
                raise CodegenError("Imprima elementos del arreglo o atributos del objeto.", node.span)
            self.emit("print", None, value, span=node.span)
        elif isinstance(node, N.ReturnStmt):
            if node.value is None:
                self.unwind(0)
                self.emit("return", span=node.span)
            else:
                value = self.convert(self.expression(node.value), self.function.return_type, node.span)
                self.unwind(0)
                self.emit("return", None, value, span=node.span)
        elif isinstance(node, (N.FunctionDecl, N.ClassDecl)):
            pass  # Los cuerpos se generan por separado, despues de _cs_entry.
        elif isinstance(node, N.IfStmt):
            other, end = self.label(), self.label()
            self.emit("ifz", None, self.expression(node.condition), target=other)
            self.statement(node.then_block)
            self.emit("jump", target=end)
            self.emit("label", target=other)
            if node.else_block:
                self.statement(node.else_block)
            self.emit("label", target=end)
        elif isinstance(node, (N.WhileStmt, N.DoWhileStmt, N.ForStmt)):
            self.loop(node)
        elif isinstance(node, N.ForEachStmt):
            self.foreach(node)
        elif isinstance(node, N.SwitchStmt):
            self.switch(node)
        elif isinstance(node, N.TryCatchStmt):
            self.try_catch(node)
        elif isinstance(node, N.BreakStmt):
            target, depth = self.breaks[-1]
            self.unwind(depth)
            self.emit("jump", target=target)
        elif isinstance(node, N.ContinueStmt):
            target, depth = self.continues[-1]
            self.unwind(depth)
            self.emit("jump", target=target)
        else:
            raise CodegenError(f"El backend MIPS no admite {node.kind} en esta fase.", node.span)

    def loop(self, node: N.WhileStmt | N.DoWhileStmt | N.ForStmt) -> None:
        start, update, end = self.label(), self.label(), self.label()
        if isinstance(node, N.ForStmt) and node.initializer:
            self.statement(node.initializer)
        self.emit("label", target=start)
        if not isinstance(node, N.DoWhileStmt) and node.condition is not None:
            self.emit("ifz", None, self.expression(node.condition), target=end)
        self.breaks.append((end, len(self.handlers)))
        self.continues.append((update, len(self.handlers)))
        if node.body:
            self.statement(node.body)
        self.continues.pop()
        self.breaks.pop()
        self.emit("label", target=update)
        if isinstance(node, N.ForStmt) and node.update:
            self.expression(node.update)
        if isinstance(node, N.DoWhileStmt):
            self.emit("ifz", None, self.expression(node.condition), target=end)
        self.emit("jump", target=start)
        self.emit("label", target=end)

    def foreach(self, node: N.ForEachStmt) -> None:
        array = self.expression(node.iterable)
        length, index = self.temp(INTEGER), self.temp(INTEGER)
        self.emit("length", length, array)
        self.emit("copy", index, Constant(0, INTEGER))
        symbol = next(s for scope in self.table.all_scopes for s in scope.symbols.values()
                      if isinstance(s, VariableSymbol) and s.name == node.variable and s.span == node.span)
        variable = self.variable(symbol)
        start, update, end = self.label(), self.label(), self.label()
        self.emit("label", target=start)
        test = self.temp(BOOLEAN)
        self.emit("<", test, index, length)
        self.emit("ifz", None, test, target=end)
        self.emit("load_index", variable, array, index)
        self.breaks.append((end, len(self.handlers)))
        self.continues.append((update, len(self.handlers)))
        self.statement(node.body)
        self.continues.pop()
        self.breaks.pop()
        self.emit("label", target=update)
        self.emit("+", index, index, Constant(1, INTEGER))
        self.emit("jump", target=start)
        self.emit("label", target=end)

    def switch(self, node: N.SwitchStmt) -> None:
        subject = self.expression(node.subject)
        end = self.label()
        labels = [self.label() for _ in node.cases]
        default = self.label() if node.default_case else end
        for case, label in zip(node.cases, labels):
            value = self.expression(case.test)
            subject_cmp, value = self.numeric_pair(subject, value, case.span)
            test, following = self.temp(BOOLEAN), self.label()
            self.emit("==", test, subject_cmp, value)
            self.emit("ifz", None, test, target=following)
            self.emit("jump", target=label)
            self.emit("label", target=following)
        self.emit("jump", target=default)
        self.breaks.append((end, len(self.handlers)))
        for case, label in zip(node.cases, labels):
            self.emit("label", target=label)
            for statement in case.statements:
                self.statement(statement)
        if node.default_case:
            self.emit("label", target=default)
            for statement in node.default_case.statements:
                self.statement(statement)
        self.breaks.pop()
        self.emit("label", target=end)

    def try_catch(self, node: N.TryCatchStmt) -> None:
        catch, end = self.label(), self.label()
        record = Place(f"_handler_{catch}", INTEGER, "handler", self.function.name)
        self.function.places.append(record)
        self.emit("try_push", None, record, target=catch, span=node.span)
        self.handlers.append(record)
        self.statement(node.try_block)
        self.handlers.pop()
        self.emit("try_pop")
        self.emit("jump", target=end)
        self.emit("label", target=catch)
        symbol = next(s for scope in self.table.all_scopes for s in scope.symbols.values()
                      if isinstance(s, VariableSymbol) and s.name == node.error_name
                      and s.span == (node.error_span or node.span))
        self.emit("catch", self.variable(symbol), span=node.span)
        self.statement(node.catch_block)
        self.emit("label", target=end)

    def assignment(self, target: N.Expression, expression: N.Expression, span: N.SourceSpan) -> Operand:
        if isinstance(target, N.Identifier):
            assert isinstance(target.resolved_symbol, VariableSymbol)
            if target.resolved_symbol.owner_class:
                field = target.resolved_symbol
                value = self.convert(self.expression(expression), field.type, span)
                self.emit("store_field", None, self.receiver(span),
                          Constant(self.field_offsets[id(field)], INTEGER), value, span=span)
                return value
            dest = self.variable(target.resolved_symbol)
            value = self.convert(self.expression(expression), dest.type, span)
            self.emit("copy", dest, value, span=span)
            return value
        if isinstance(target, N.IndexExpr):
            array, index = self.expression(target.target), self.expression(target.index)
            assert isinstance(array.type, ArrayType)
            value = self.convert(self.expression(expression), array.type.element, span)
            self.emit("store_index", None, array, index, value, span=span)
            return value
        if isinstance(target, N.PropertyAccess):
            receiver = self.expression(target.target)
            assert isinstance(receiver.type, ClassType)
            field = self.table.classes.lookup_field(receiver.type.class_name, target.name)
            assert field is not None
            value = self.convert(self.expression(expression), field.type, span)
            self.emit("store_field", None, receiver, Constant(self.field_offsets[id(field)], INTEGER), value, span=span)
            return value
        raise CodegenError("Destino de asignacion no implementado en MIPS.", span)

    def numeric_pair(self, left: Operand, right: Operand, span: N.SourceSpan) -> tuple[Operand, Operand]:
        if FLOAT in (left.type, right.type):
            return self.convert(left, FLOAT, span), self.convert(right, FLOAT, span)
        return left, right

    def expression(self, node: N.Expression) -> Operand:
        type_ = node.resolved_type
        assert type_ is not None
        if isinstance(node, (N.IntegerLiteral, N.FloatLiteral, N.StringLiteral, N.BooleanLiteral)):
            if isinstance(node, N.IntegerLiteral) and not -(2**31) <= node.value < 2**31:
                raise CodegenError("El entero no cabe en 32 bits con signo.", node.span)
            if isinstance(node, N.FloatLiteral) and (not math.isfinite(node.value) or abs(node.value) > 3.402823466e38):
                raise CodegenError("El float no cabe en precision simple MIPS.", node.span)
            if isinstance(node, N.StringLiteral) and "\0" in node.value:
                raise CodegenError("Las cadenas MIPS no admiten caracteres NUL internos.", node.span)
            return Constant(node.value, type_)
        if isinstance(node, N.NullLiteral):
            return Constant(None, NULL)
        if isinstance(node, N.ThisExpr):
            result = self.temp(type_)
            self.emit("copy", result, self.receiver(node.span), span=node.span)
            return result
        if isinstance(node, N.NewExpr):
            constructor = self.table.classes.lookup_constructor(node.class_name)
            args = [self.convert(self.expression(arg), parameter.type, arg.span)
                    for arg, parameter in zip(node.arguments, constructor.parameters)] if constructor else []
            result = self.temp(type_)
            size = 4 * (1 + len(self.class_fields[node.class_name]))
            if size > 32760:
                raise CodegenError("El objeto excede los desplazamientos de 16 bits de MIPS.", node.span)
            self.emit("new_object", result, Constant(size, INTEGER), target=node.class_name, span=node.span)
            self.emit("call", None, result, target=self.initializers[node.class_name].name, span=node.span)
            if constructor:
                self.emit("call", None, result, *args, target=self.function_names[id(constructor)], span=node.span)
            return result
        if isinstance(node, N.PropertyAccess):
            receiver = self.expression(node.target)
            assert isinstance(receiver.type, ClassType)
            field = self.table.classes.lookup_field(receiver.type.class_name, node.name)
            if field is None:
                raise CodegenError("Invoque el metodo con parentesis; los metodos no se usan como valores.", node.span)
            result = self.temp(type_)
            self.emit("load_field", result, receiver, Constant(self.field_offsets[id(field)], INTEGER), span=node.span)
            return result
        if isinstance(node, N.Identifier):
            if not isinstance(node.resolved_symbol, VariableSymbol):
                raise CodegenError("Solo se admiten llamadas directas a funciones; no valores de funcion.", node.span)
            # Congelar lecturas antes de evaluar operandos con efectos laterales.
            result = self.temp(type_)
            if node.resolved_symbol.owner_class:
                self.emit("load_field", result, self.receiver(node.span),
                          Constant(self.field_offsets[id(node.resolved_symbol)], INTEGER), span=node.span)
            else:
                self.emit("copy", result, self.variable(node.resolved_symbol), span=node.span)
            return result
        if isinstance(node, N.UnaryExpr):
            if node.operator == "-" and isinstance(node.operand, N.IntegerLiteral) and node.operand.value == 2**31:
                return Constant(-(2**31), INTEGER)
            value = self.expression(node.operand)
            if node.operator == "+":
                return value
            result = self.temp(type_)
            self.emit("neg" if node.operator == "-" else "!", result, value, span=node.span)
            return result
        if isinstance(node, N.BinaryExpr):
            if node.operator in ("&&", "||"):
                return self.short_circuit(node)
            left, right = self.expression(node.left), self.expression(node.right)
            result = self.temp(type_)
            if node.operator == "+" and type_ == STRING:
                left, right = self.stringify(left, node.span), self.stringify(right, node.span)
                self.emit("concat", result, left, right, span=node.span)
            else:
                left, right = self.numeric_pair(left, right, node.span)
                if node.operator == "%" and left.type == FLOAT:
                    raise CodegenError("El modulo MIPS de esta fase requiere operandos integer.", node.span)
                self.emit(node.operator, result, left, right, span=node.span)
            return result
        if isinstance(node, N.TernaryExpr):
            result, other, end = self.temp(type_), self.label(), self.label()
            self.emit("ifz", None, self.expression(node.condition), target=other)
            self.emit("copy", result, self.convert(self.expression(node.then_expr), type_, node.span))
            self.emit("jump", target=end)
            self.emit("label", target=other)
            self.emit("copy", result, self.convert(self.expression(node.else_expr), type_, node.span))
            self.emit("label", target=end)
            return result
        if isinstance(node, N.AssignExpr):
            return self.assignment(node.target, node.value, node.span)
        if isinstance(node, N.CallExpr):
            receiver = None
            if isinstance(node.callee, N.PropertyAccess):
                receiver = self.expression(node.callee.target)
                assert isinstance(receiver.type, ClassType)
                symbol = self.table.classes.lookup_method(receiver.type.class_name, node.callee.name)
            elif isinstance(node.callee, N.Identifier) and isinstance(node.callee.resolved_symbol, FunctionSymbol):
                symbol = node.callee.resolved_symbol
                if symbol.owner_class:
                    receiver = self.receiver(node.span)
            else:
                raise CodegenError("Las funciones y metodos deben invocarse por su nombre.", node.span)
            assert symbol is not None
            hidden: list[Operand] = []
            function = self.callables[id(symbol)]
            if function.parent is not None:
                link = self.temp(INTEGER)
                self.emit("frame_ref", link, target=function.parent, span=node.span)
                hidden.append(link)
            if receiver is not None:
                hidden.append(receiver)
            args = [self.convert(self.expression(arg), parameter.type, arg.span)
                    for arg, parameter in zip(node.arguments, symbol.parameters)]
            result = self.temp(type_) if type_ != VOID else None
            if receiver is not None:
                self.emit("vcall", result, *hidden, *args, target=str(self.method_slots[symbol.name]), span=node.span)
            else:
                self.emit("call", result, *hidden, *args, target=function.name, span=node.span)
            return result if result is not None else Constant(0, VOID)
        if isinstance(node, N.ArrayLiteral):
            assert isinstance(type_, ArrayType)
            result = self.temp(type_)
            self.emit("new_array", result, Constant(len(node.elements), INTEGER), span=node.span)
            for index, element in enumerate(node.elements):
                value = self.convert(self.expression(element), type_.element, element.span)
                self.emit("store_index", None, result, Constant(index, INTEGER), value, span=element.span)
            return result
        if isinstance(node, N.IndexExpr):
            array, index = self.expression(node.target), self.expression(node.index)
            result = self.temp(type_)
            self.emit("load_index", result, array, index, span=node.span)
            return result
        raise CodegenError(f"El backend MIPS no admite la expresion {node.kind}.", node.span)

    def stringify(self, value: Operand, span: N.SourceSpan) -> Operand:
        if value.type == STRING:
            return value
        if value.type not in (INTEGER, BOOLEAN, NULL):
            raise CodegenError("La concatenacion MIPS admite string, integer, boolean y null; use print para float.", span)
        result = self.temp(STRING)
        self.emit("to_string", result, value, span=span)
        return result

    def short_circuit(self, node: N.BinaryExpr) -> Operand:
        result, other, end = self.temp(BOOLEAN), self.label(), self.label()
        left = self.expression(node.left)
        self.emit("ifz", None, left, target=other)
        if node.operator == "&&":
            self.emit("copy", result, self.expression(node.right))
        else:
            self.emit("copy", result, Constant(True, BOOLEAN))
        self.emit("jump", target=end)
        self.emit("label", target=other)
        if node.operator == "&&":
            self.emit("copy", result, Constant(False, BOOLEAN))
        else:
            self.emit("copy", result, self.expression(node.right))
        self.emit("label", target=end)
        return result


def generate_ir(ast: N.Program, table: SymbolTable) -> IRProgram:
    return IRGenerator(table).generate(ast)
