from dataclasses import dataclass, field
from typing import List, Optional
from lexer_2 import Token, token_Type 
from symbols_table import SymbolTable, SymbolType

class ASTNode:
    pass

@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

@dataclass
class IfNode(ASTNode):
    condition: ASTNode
    then_branch: ASTNode
    else_branch: Optional[ASTNode] = None

class ReturnNode(ASTNode):
    expression: ASTNode


@dataclass
class BinaryOpNode(ASTNode):
    left: ASTNode
    op: Token
    right: ASTNode

@dataclass
class NumberNode(ASTNode):
    token: Token
    @property
    def value(self) -> float: return float(self.token.value)

@dataclass
class STRNode(ASTNode): 
    token: Token
    @property
    def value(self) -> str: return self.token.value

@dataclass
class FStringNode(ASTNode): 
    original_token: Token 
   
    @property
    def raw_content(self) -> str: return self.original_token.value

@dataclass
class UnaryOpNode(ASTNode):
    op: Token
    expr: ASTNode

@dataclass
class VariableNode(ASTNode):
    name: str
    token: Token

@dataclass
class AssignmentNode(ASTNode):
    variable_name: str
    variable_token: Token
    expression: ASTNode

@dataclass
class printNode(ASTNode):
    expressions: List[ASTNode] 

@dataclass
class BlockNode(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

@dataclass
class FunctionDefNode(ASTNode):
    name: str
    parameters: List[str]
    param_tokens: List[Token]
    body: BlockNode 
    func_token: Token

class PushdownParser:
    def __init__(self, tokens: List[Token], symbol_table: SymbolTable):
        self.tokens = tokens
        self.pos = 0
        self.current_token: Optional[Token] = self.tokens[0] if tokens else None
        self.symbol_table = symbol_table

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            
            self.current_token = self.tokens[self.pos -1] if self.tokens and self.tokens[self.pos-1].type == token_Type.EOF else None


    def error(self, message: str, token: Optional[Token] = None):
        tok_err = token or self.current_token
        pos_info = "al final del archivo (inesperado)"
        if tok_err:
             pos_info = f"en línea {tok_err.ln}, columna {tok_err.col} (token: '{tok_err.value}', tipo: {tok_err.type.name})"
        raise SyntaxError(f"Error de Sintaxis: {message} {pos_info}")

    def eat(self, expected_type: token_Type) -> Token:
        if self.current_token and self.current_token.type == expected_type:
            token_val = self.current_token
            self.advance()
            return token_val
        else:
            expected_name = expected_type.name
            found_val = self.current_token.value if self.current_token else "None"
            found_type_name = self.current_token.type.name if self.current_token else ("EOF" if self.pos >= len(self.tokens) else "None")
            self.error(f"Se esperaba token de tipo {expected_name}, pero se encontró '{found_val}' (tipo {found_type_name})")
            
            raise RuntimeError("Unreachable code in eat()")


    def parse_program(self) -> ProgramNode:
        statements = self.parse_statement_list()
        
        if self.current_token and self.current_token.type != token_Type.EOF:
             self.error(f"Se esperaba el fin del archivo después de las sentencias, pero se encontró {self.current_token.type.name}")
        return ProgramNode(statements=statements)

    def parse_statement_list(self) -> List[ASTNode]:
        statements = []
        
        while self.current_token and self.current_token.type not in (token_Type.EOF, token_Type.TOK_RIGHT_BRACE):
             statements.append(self.parse_statement())
        return statements

    def parse_statement(self) -> ASTNode:
        token_stat = self.current_token
        if not token_stat:
             self.error("Se esperaba una sentencia, pero se encontró el fin del archivo.")

        if token_stat.type == token_Type.KEYWORD:
            if token_stat.value == 'print':
                return self.parse_print_statement()
            elif token_stat.value == 'fun':
                return self.parse_function_definition()
            elif token_stat.value == 'if':
                return self.parse_if_statement()
            elif token_stat.value == 'return':
                return self.parse_return_statement()
                    
            else:
                 self.error(f"Palabra clave inesperada '{token_stat.value}' al inicio de una sentencia")
        elif token_stat.type == token_Type.TOK_LEFT_BRACE:
            return self.parse_block_statement()

        elif token_stat.type == token_Type.IDENTIFIER and \
             self.pos + 1 < len(self.tokens) and \
             self.tokens[self.pos+1].type == token_Type.TOK_EQUAL:
            return self.parse_assignment_statement()
        else: 
            expr = self.parse_expression()
            self.eat(token_Type.TOK_SEMICOMMA)
            return expr 
    def parse_print_statement(self) -> printNode:
        self.eat(token_Type.KEYWORD) 
        start_paren_token = self.eat(token_Type.TOK_LEFT_PAREN)
        
        expressions_list: List[ASTNode] = []
        
        if self.current_token and self.current_token.type != token_Type.TOK_RIGHT_PAREN:
            expressions_list.append(self.parse_expression())
            while self.current_token and self.current_token.type == token_Type.TOK_COMMA:
                self.eat(token_Type.TOK_COMMA)
                expressions_list.append(self.parse_expression())
        
        self.eat(token_Type.TOK_RIGHT_PAREN)
        self.eat(token_Type.TOK_SEMICOMMA)
            
        return printNode(expressions=expressions_list)

    def parse_block_statement(self) -> BlockNode:
        self.eat(token_Type.TOK_LEFT_BRACE)
        self.symbol_table.enter_scope()
        statements = self.parse_statement_list()
        self.symbol_table.exit_scope()
        self.eat(token_Type.TOK_RIGHT_BRACE)
        return BlockNode(statements=statements)
    
    def parse_if_statement(self) -> IfNode:
        self.eat(token_Type.KEYWORD)  # consume 'if'
        condition = self.parse_expression()  # parsea la condición (que usa operadores de comparación)
        then_branch = self.parse_block_statement()  # parsea el bloque
        self.eat(token_Type.TOK_SEMICOMMA)
        else_branch = None
        if self.current_token and self.current_token.value == "else":
            self.eat(token_Type.KEYWORD)  # consume 'else'
            else_branch = self.parse_block_statement()
        
        return IfNode(condition, then_branch, else_branch)
    def parse_return_statement(self) -> ReturnNode:
        self.eat(token_Type.KEYWORD)
        expr = self.parse_expression()
        self.eat(token_Type.TOK_SEMICOMMA)
        return ReturnNode(expression=expr)
    
    def parse_function_definition(self) -> FunctionDefNode:
        func_token = self.eat(token_Type.KEYWORD) # 'fun'
        name_token = self.eat(token_Type.IDENTIFIER)
        func_name = name_token.value
        
        func_symbol = self.symbol_table.define(func_name, SymbolType.FUNCTION, node=None) 

        self.eat(token_Type.TOK_LEFT_PAREN)
        parameters: List[str] = []
        param_tokens_list: List[Token] = []
        if self.current_token and self.current_token.type != token_Type.TOK_RIGHT_PAREN:
            param_id_token = self.eat(token_Type.IDENTIFIER)
            parameters.append(param_id_token.value)
            param_tokens_list.append(param_id_token)
            while self.current_token and self.current_token.type == token_Type.TOK_COMMA:
                self.eat(token_Type.TOK_COMMA)
                param_id_token = self.eat(token_Type.IDENTIFIER)
                parameters.append(param_id_token.value)
                param_tokens_list.append(param_id_token)
        self.eat(token_Type.TOK_RIGHT_PAREN)

        
        self.symbol_table.enter_scope()
        for p_name, p_token in zip(parameters, param_tokens_list):
            self.symbol_table.define(p_name, SymbolType.VARIABLE, node=p_token) 

        
        if not (self.current_token and self.current_token.type == token_Type.TOK_LEFT_BRACE):
            self.error("Se esperaba '{' para el cuerpo de la función.")
        
        
        body_block_node = self._parse_block_content_for_func()
        self.eat(token_Type.TOK_SEMICOMMA)

        self.symbol_table.exit_scope() 

        node = FunctionDefNode(
            name=func_name,
            parameters=parameters,
            param_tokens=param_tokens_list,
            body=body_block_node,
            func_token=func_token
        )
        func_symbol.node = node 
        return node

    def _parse_block_content_for_func(self) -> BlockNode:
        
        self.eat(token_Type.TOK_LEFT_BRACE)
        statements = self.parse_statement_list()
        self.eat(token_Type.TOK_RIGHT_BRACE)
        return BlockNode(statements=statements)


    def parse_assignment_statement(self) -> AssignmentNode:
        var_token = self.eat(token_Type.IDENTIFIER)
        var_name = var_token.value
        self.eat(token_Type.TOK_EQUAL)
        expr = self.parse_expression()
        self.eat(token_Type.TOK_SEMICOMMA)
        
        symbol = self.symbol_table.lookup(var_name)
        if not symbol: 
             self.symbol_table.define(var_name, SymbolType.VARIABLE, node=var_token)
        elif symbol.type == SymbolType.FUNCTION: 
             self.error(f"No se puede asignar a '{var_name}' porque es una función.", var_token)
        
        return AssignmentNode(variable_name=var_name, variable_token=var_token, expression=expr)

    def parse_expression(self) -> ASTNode: 
        return self.parse_comparison()
    def parse_comparison(self) -> ASTNode:
        node = self.parse_addition()
        while self.current_token and self.current_token.type in (
            token_Type.TOK_GREAT_EQUAL, token_Type.TOK_LESS_EQUAL,
            token_Type.TOK_EQUAL_EQUAL, token_Type.TOK_GREAT, token_Type.TOK_LESS
        ):
            op_token = self.current_token
            self.eat(op_token.type)
            right_node = self.parse_addition()
            node = BinaryOpNode(left=node, op=op_token, right=right_node)
        return node
    def parse_addition(self) -> ASTNode:  # ← NUEVO MÉTODO
        node = self.parse_term()
        while self.current_token and self.current_token.type in (token_Type.TOK_PLUS, token_Type.TOK_MINUS):
            op_token = self.current_token
            self.eat(op_token.type) 
            right_node = self.parse_term()
            node = BinaryOpNode(left=node, op=op_token, right=right_node)
        return node

    def parse_term(self) -> ASTNode: 
        node = self.parse_factor()
        while self.current_token and self.current_token.type in (token_Type.TOK_MULT, token_Type.TOK_DIV):
            op_token = self.current_token
            self.eat(op_token.type) 
            right_node = self.parse_factor()
            node = BinaryOpNode(left=node, op=op_token, right=right_node)
        return node
    def parse_factor(self) -> ASTNode: 
        token_fact = self.current_token
        if not token_fact: self.error("Factor inesperado: fin de archivo.")

        if token_fact.type in (token_Type.TOK_PLUS, token_Type.TOK_MINUS): 
            op_token = token_fact
            self.eat(op_token.type)
            expr_node = self.parse_factor() 
            return UnaryOpNode(op=op_token, expr=expr_node)
        else: 
            return self.parse_atom()

    def parse_atom(self) -> ASTNode: 
        token_atom = self.current_token
        if not token_atom: self.error("Átomo inesperado: fin de archivo.")

        if token_atom.type == token_Type.NUM:
            self.eat(token_Type.NUM)
            return NumberNode(token=token_atom)
        elif token_atom.type == token_Type.STRING: 
            self.eat(token_Type.STRING)
            return STRNode(token=token_atom)
        
        elif token_atom.type == token_Type.TOK_F_STRING: 
            self.eat(token_Type.TOK_F_STRING)
            return FStringNode(original_token=token_atom)
        
        elif token_atom.type == token_Type.IDENTIFIER:
            self.eat(token_Type.IDENTIFIER)
            return VariableNode(name=token_atom.value, token=token_atom)
        
        elif token_atom.type == token_Type.TOK_LEFT_PAREN:
            self.eat(token_Type.TOK_LEFT_PAREN)
            expr_node = self.parse_expression()
            self.eat(token_Type.TOK_RIGHT_PAREN)
            return expr_node
        else:
            self.error(f"Token inesperado '{token_atom.value}' (tipo {token_atom.type.name}), se esperaba número, string, f-string, identificador o '('")
            raise RuntimeError("Unreachable") 

