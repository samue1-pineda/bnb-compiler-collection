import sys
from lexer_2 import Lexer, Token 
from symbols_table import SymbolTable
from anilizador_sintactico import PushdownParser, ASTNode 
from codegen import CodeGenerator
import json

def ast_to_dict_serializable(node):
    if isinstance(node, list):
        return [ast_to_dict_serializable(n) for n in node]
    if not isinstance(node, ASTNode): 
        if isinstance(node, Token): 
            return f"Token({node.type.name}, '{node.value}', Ln:{node.ln}, Col:{node.col})"
        try: #Intenta convertir a string otros tipos básicos si no son Nodos
            return str(node)
        except:
            return f"NonSerializableType({type(node).__name__})"

    d = {'node_type': type(node).__name__}
    if hasattr(node, '__dict__'):
        for k, v in node.__dict__.items():
            if k.startswith('_') or callable(v): #omite atributos privados o métodos,
                #esto es implementado para el siguiente paso de mi compilador que son los objetos 
                continue
            d[k] = ast_to_dict_serializable(v) 
    elif hasattr(node, '__slots__'): 
        for slot in node.__slots__:
            if slot.startswith('_') or callable(getattr(node, slot)):
                continue
            d[slot] = ast_to_dict_serializable(getattr(node, slot))
    return d


def compilar_a_bnb(archivo_entrada: str, nombre_base_salida: str): 
    print(f"Compilando '{archivo_entrada}'...")

    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            codigo_fuente = f.read()
        print("Código fuente leído.")

        lexer = Lexer(codigo_fuente)
        tokens = lexer.tokenize()
        """
        print(f"DEBUG: Tokens generados: {len(tokens)}")  
        for i, tok in enumerate(tokens[:10]):  # Muestra los primeros 10
            print(f"  Token {i}: {tok.type.name} = '{tok.value}'")
        """
        print("Análisis léxico completado.")

        symbol_table = SymbolTable()
        parser = PushdownParser(tokens, symbol_table)
        ast = parser.parse_program()
        print("AST generado")

        #generacion del AST en formato JSON 
        archivo_ast_salida = nombre_base_salida + ".ast.json" 
        try:
            ast_dict = ast_to_dict_serializable(ast)
            with open(archivo_ast_salida, 'w', encoding='utf-8') as f_ast:
                json.dump(ast_dict, f_ast, indent=2)
        except Exception as e_ast:
            print(f"Error al serializar o escribir el AST: {e_ast}")
            import traceback
            traceback.print_exc()


 
        code_generator = CodeGenerator(symbol_table)
        codigo_bnb = code_generator.generate(ast)
        print("Generación de código .BNB completado")

        archivo_asm_salida = nombre_base_salida + ".bnbASM" 
        try:
            with open(archivo_asm_salida, 'w', encoding='utf-8') as f_asm:
                for instruccion in codigo_bnb:
                    f_asm.write(instruccion + '\n')
            
        except IOError as e_io:
            print(f"Error: No se pudo escribir en el archivo de salida '{archivo_asm_salida}'. Razón: {e_io}")
            sys.exit(1)
        
       
        print(f"COMPILE SUCESS CODE 0")
    except FileNotFoundError:
        print(f"Error: El archivo de entrada '{archivo_entrada}' no fue encontrado.")
        sys.exit(1)
    except (SyntaxError, NameError, TypeError, NotImplementedError)     as e_comp:
        print(f"\nError de Compilación: {e_comp}")
        #print del traceback para ver el error en la línea exacta
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e_gen:
        print(f"\nOcurrió un error inesperado durante la compilación: {e_gen}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python bnb_compile_collect.py <archivo_fuente.bnb>") 
        sys.exit(1)

    archivo_fuente = sys.argv[1]
    if '.' in archivo_fuente:
        base_nombre = archivo_fuente.rsplit('.', 1)[0]
    else:
        base_nombre = archivo_fuente
    
    compilar_a_bnb(archivo_fuente, base_nombre)