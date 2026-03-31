from typing import Any
from lexer_2 import token_Type
from anilizador_sintactico import ASTNode, BinaryOpNode, NumberNode, UnaryOpNode

class Interpreter:
    def __init__(self, ast: ASTNode):
        self.ast = ast
    
    def visit_BinaryOpNode(self, node: BinaryOpNode) -> float:
        if node.op.type == token_Type.TOK_PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == token_Type.TOK_MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == token_Type.TOK_MULT:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == token_Type.TOK_DIV:
            right_val = self.visit(node.right)
            if right_val == 0:
                raise Exception("Error semántico: División por cero")
            return self.visit(node.left) / right_val
    
    def visit_NumberNode(self, node: NumberNode) -> float:
        return node.value
    
    def visit_UnaryOpNode(self, node: UnaryOpNode) -> float:
        if node.op.type == token_Type.TOK_PLUS:
            return +self.visit(node.expr)
        elif node.op.type == token_Type.TOK_MINUS:
            return -self.visit(node.expr)
    
    def visit(self, node: ASTNode) -> float:
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node: ASTNode) -> Any:
        raise Exception(f"No hay método visit_{type(node).__name__}")
    
    def interpret(self) -> float:
        return self.visit(self.ast)

