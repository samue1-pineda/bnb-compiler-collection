from anilizador_sintactico import (
    ASTNode, ProgramNode, BinaryOpNode, NumberNode, UnaryOpNode, 
    STRNode, FStringNode, printNode, VariableNode, AssignmentNode, 
    BlockNode, FunctionDefNode,IfNode,ReturnNode, token_Type
)
from symbols_table import SymbolTable, SymbolType 
from typing import List, Any, Union, Dict
import re 
#TODO documentar, solo dios recuerda que hacia toda esta barbaridad
#Dias sin documentar: 1
#inicio 08/04/26

class CodeGenerator:
    def __init__(self, symbol_table: SymbolTable):
        self.instructions: List[str] = []
        self.symbol_table = symbol_table
        self.label_count = 0
        self.simulation_env_stack: List[Dict[str, Union[float, str]]] = [{}]

    @property
    def current_simulation_env(self) -> Dict[str, Union[float, str]]:
        
        if not self.simulation_env_stack: 
            self.simulation_env_stack.append({})
        return self.simulation_env_stack[-1]

    def _get_simulated_variable(self, name: str) -> Union[float, str, None]:
        """Busca una variable en la pila de entornos, del más local al más global."""
        for env in reversed(self.simulation_env_stack):
            if name in env:
                return env[name]
        
        return None 

    def _set_simulated_variable(self, name: str, value: Union[float, str]):
        """Establece una variable en el entorno de simulación del scope actual."""
        self.current_simulation_env[name] = value

    def _enter_simulated_scope(self):
        self.simulation_env_stack.append({})

    def _exit_simulated_scope(self):
        if len(self.simulation_env_stack) > 1: 
            self.simulation_env_stack.pop()

    def add_instruction(self, instruction: str):
        self.instructions.append(instruction)

    def visit(self, node: ASTNode) -> Any: 
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        raise NotImplementedError(f"CodeGen: Método visit_{type(node).__name__} no implementado para {node}")

    def visit_ProgramNode(self, node: ProgramNode):
        self.add_instruction("; Inicio del programa BNB")
        self.simulation_env_stack = [{}] 
        for statement in node.statements:
            self.visit(statement)
        self.add_instruction("EOF ';'Fin del programa")
        return None

    def visit_NumberNode(self, node: NumberNode) -> float:
        self.add_instruction(f"PUSH_NUM {node.value}")
        return node.value

    def visit_STRNode(self, node: STRNode) -> str:
        
        escaped_for_asm = node.value.replace('"', '\\"')
        self.add_instruction(f'PUSH_STR "{escaped_for_asm}"')
        return node.value 
    def visit_FStringNode(self, node: FStringNode) -> str:
        simulated_string_parts = []
        generated_code_segments = 0 
        last_idx = 0
        for match in re.finditer(r"\{(.*?)\}", node.raw_content):
            start_match, end_match = match.span()
            expr_in_fstring_str = match.group(1).strip() 

            
            if start_match > last_idx:
                literal_part_val = node.raw_content[last_idx:start_match]
                simulated_string_parts.append(literal_part_val)
                self.add_instruction(f'PUSH_STR "{literal_part_val.replace("\"", "\\\"")}"')
                generated_code_segments += 1
            
            
            if expr_in_fstring_str.isidentifier(): 
                var_name_in_fstring = expr_in_fstring_str
                
                sim_var_val = self._get_simulated_variable(var_name_in_fstring)
                simulated_string_parts.append(str(sim_var_val) if sim_var_val is not None else f"{{{var_name_in_fstring}}}")
                
                #Código BNB
                var_symbol_lookup = self.symbol_table.lookup(var_name_in_fstring)
                if var_symbol_lookup and var_symbol_lookup.type == SymbolType.VARIABLE:
                    self.add_instruction(f"LOAD {var_name_in_fstring}")
                    self.add_instruction("TO_STR ;")
                else: 
                    self.add_instruction(f'PUSH_STR "{{{var_name_in_fstring}}}"')
                generated_code_segments += 1
            else: 
                placeholder_expr_val = f"{{{expr_in_fstring_str}}}"
                simulated_string_parts.append(placeholder_expr_val)
                self.add_instruction(f'PUSH_STR "{placeholder_expr_val.replace("\"", "\\\"")}"')
                generated_code_segments += 1
            last_idx = end_match
            
        if last_idx < len(node.raw_content):
            literal_part_val = node.raw_content[last_idx:]
            simulated_string_parts.append(literal_part_val)
            self.add_instruction(f'PUSH_STR "{literal_part_val.replace("\"", "\\\"")}"')
            generated_code_segments += 1

        if generated_code_segments == 0:
            if node.raw_content: 
                simulated_string_parts.append(node.raw_content)
                self.add_instruction(f'PUSH_STR "{node.raw_content.replace("\"", "\\\"")}"')
            else: 
                simulated_string_parts.append("")
                self.add_instruction('PUSH_STR ""')
            generated_code_segments = 1 

        if generated_code_segments > 1:
            self.add_instruction(f"CONCAT {generated_code_segments} ; (concatenar)")
        
        return "".join(simulated_string_parts) 


    def visit_VariableNode(self, node: VariableNode) -> Union[float, str, None]:
        symbol = self.symbol_table.lookup(node.name)
        if not symbol:
            raise NameError(f"CodeGen: Variable '{node.name}' no definida al usarla.")
        self.add_instruction(f"LOAD {node.name}")
        return self._get_simulated_variable(node.name)
    def visit_IfNode(self, node: IfNode):
        label_id = self.label_count
        self.label_count += 1
        
        label_else = f"ELSE_{label_id}"
        label_end = f"END_IF_{label_id}"
        self.visit(node.condition)
    

        self.add_instruction(f"JZ {label_else} ; Saltar si es falso")
        

        self.visit(node.then_branch)
        self.add_instruction(f"JMP {label_end}")
        
        # 4. Rama Falsa
        self.add_instruction(f"{label_else}:")
        if node.else_branch:
            self.visit(node.else_branch)
        
        self.add_instruction(f"{label_end}:")

    def visit_ReturnNode(self, node: ReturnNode):
        self.visit(node.expression)
        self.add_instruction("RET ; Devolver valor en el tope de la pila")
    def visit_AssignmentNode(self, node: AssignmentNode):
        expr_value_sim = self.visit(node.expression) 
        
        if expr_value_sim is not None: 
            self._set_simulated_variable(node.variable_name, expr_value_sim)
        
        
        symbol = self.symbol_table.lookup(node.variable_name)
        if not symbol:
            
             self.symbol_table.define(node.variable_name, SymbolType.VARIABLE, node=node.variable_token)
        elif symbol.type != SymbolType.VARIABLE:
             raise TypeError(f"CodeGen: No se puede asignar a '{node.variable_name}' (no es variable).")
        
        self.add_instruction(f"STORE {node.variable_name}")
        return None 

    def visit_BinaryOpNode(self, node: BinaryOpNode) -> Union[float, None]:
        left_val_sim = self.visit(node.left)
        right_val_sim = self.visit(node.right)
        
        op_type = node.op.type
        
        if op_type == token_Type.TOK_PLUS: 
            self.add_instruction("ADD")
        elif op_type == token_Type.TOK_MINUS: 
            self.add_instruction("SUB")
        elif op_type == token_Type.TOK_MULT: 
            self.add_instruction("MUL")
        elif op_type == token_Type.TOK_DIV: 
            self.add_instruction("DIV")
        elif op_type == token_Type.TOK_GREAT_EQUAL: 
            self.add_instruction("GE")
        elif op_type == token_Type.TOK_LESS_EQUAL: 
            self.add_instruction("LE")
        elif op_type == token_Type.TOK_EQUAL_EQUAL: 
            self.add_instruction("EQ")
        elif op_type == token_Type.TOK_GREAT: 
            self.add_instruction("GT")
        elif op_type == token_Type.TOK_LESS: 
            self.add_instruction("LT")
        else: 
            raise NotImplementedError(f"CodeGen: Operador binario {node.op.type.name} no soportado.")

        # Simulación
        if isinstance(left_val_sim, (int, float)) and isinstance(right_val_sim, (int, float)):
            if op_type == token_Type.TOK_PLUS: 
                return left_val_sim + right_val_sim
            elif op_type == token_Type.TOK_MINUS: 
                return left_val_sim - right_val_sim
            elif op_type == token_Type.TOK_MULT: 
                return left_val_sim * right_val_sim
            elif op_type == token_Type.TOK_DIV:
                if right_val_sim == 0:
                    print("[ERR]: División por cero.")
                    return None
                return left_val_sim / right_val_sim
            elif op_type == token_Type.TOK_GREAT_EQUAL: 
                return 1 if left_val_sim >= right_val_sim else 0
            elif op_type == token_Type.TOK_LESS_EQUAL: 
                return 1 if left_val_sim <= right_val_sim else 0
            elif op_type == token_Type.TOK_EQUAL_EQUAL: 
                return 1 if left_val_sim == right_val_sim else 0
            elif op_type == token_Type.TOK_GREAT: 
                return 1 if left_val_sim > right_val_sim else 0
            elif op_type == token_Type.TOK_LESS: 
                return 1 if left_val_sim < right_val_sim else 0
            
        return None
    
    def visit_UnaryOpNode(self, node: UnaryOpNode) -> Union[float, None]:
        expr_val_sim = self.visit(node.expr)
        op_type = node.op.type
        
        if op_type == token_Type.TOK_MINUS: self.add_instruction("NEG") 
        elif op_type == token_Type.TOK_PLUS: pass 
        else: raise NotImplementedError(f"CodeGen: Operador unario {node.op.type.name} no soportado.")

        if isinstance(expr_val_sim, (int, float)):
            if op_type == token_Type.TOK_MINUS: return -expr_val_sim
            elif op_type == token_Type.TOK_PLUS: return +expr_val_sim 
        return None

    def visit_printNode(self, node: printNode):
        simulated_outputs_for_print = []
        num_expressions_to_print = len(node.expressions)

        if num_expressions_to_print == 0:
            print() 
            self.add_instruction("PRINT_NL ; NUEVA LINEA")
            return None

        for expr_node in node.expressions:
            
            sim_val_for_expr = self.visit(expr_node)
            simulated_outputs_for_print.append(str(sim_val_for_expr) if sim_val_for_expr is not None else "None")
        
        if num_expressions_to_print == 1:
            self.add_instruction("PRINT_ONE ;")
        elif num_expressions_to_print > 1:
            
            self.add_instruction(f"PRINT_ARGS {num_expressions_to_print} ;")

        #I/O de la consola del compilador
        if simulated_outputs_for_print:
            print(" ".join(simulated_outputs_for_print)) 
        return None


    def visit_BlockNode(self, node: BlockNode):
        self.symbol_table.enter_scope()      
        self._enter_simulated_scope()        

        for statement in node.statements:
            self.visit(statement)
        
        self._exit_simulated_scope()
        self.symbol_table.exit_scope()
        return None

    def visit_FunctionDefNode(self, node: FunctionDefNode):
        func_label = f"FUNC_{node.name.upper()}"

        self.add_instruction(f"\n{func_label}:")
        self.add_instruction(f"; -- Definición de Función {node.name} --")

        
        self.visit(node.body)
        
        self.add_instruction(f"RET ; Retorno de {node.name}")
        self.add_instruction(f"; -- Fin Definición de Función {node.name} --\n")
        return None


    def generate(self, ast: ASTNode) -> List[str]:
        self.instructions = []
        self.simulation_env_stack = [{}] 
        self.visit(ast)
        return self.instructions
