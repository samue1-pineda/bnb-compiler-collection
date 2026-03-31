from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional#FIXME

class token_Type(Enum):
    NUM = auto()
    TOK_PLUS = auto()  # +
    TOK_MINUS = auto()#  -
    TOK_DIV = auto() #  /
    TOK_MULT = auto()  # *

    TOK_EQUAL=auto() # =

    TOK_LEFT_PAREN = auto()  # (
    TOK_RIGHT_PAREN = auto()  # )
    TOK_RIGHT_BRACE=auto()# }
    TOK_LEFT_BRACE=auto()#{
    


    IDENTIFIER = auto()  # literals o variables o funciones

    STRING= auto()  # cadena de texto
    TOK_F_STRING = auto()  #print(f"")
    TOK_COMMA = auto()  # ,
    TOK_SEMICOMMA = auto()  # ;
    KEYWORD = auto()  # palabras reservadas
    EOF = auto()  # fin del archivo

@dataclass  # lo mas cercano a un struct que encontre
class Token:
    type: token_Type
    value: str
    ln: int
    col: int

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos_ = 0
        self.Ln = 1 #LINEA
        self.Col = 1 #COLUMNA
        self.current_char = self.text[0] if text else None
        self.keywords = {
        'print': token_Type.KEYWORD,
        'fun':token_Type.KEYWORD,
        'if':token_Type.KEYWORD
        } #def palabras claves
        
    def advance(self):
        #avanza linea y columna como hace vscode
        if self.current_char == '\n':
            self.Ln += 1
            self.Col = 0
        self.pos_+= 1
        if self.pos_ < len(self.text):
            self.current_char = self.text[self.pos_]
            if self.current_char == '\n':
                self.Col=1
            elif self.pos_ >0 and self.text[self.pos_-1]== '\n':
                self.Col=1
            else:
                self.Col+=1
        else:
            self.current_char = None  # NULL o VOID 

    def peek(self):
        peek_pos = self.pos_ + 1
        if peek_pos < len(self.text):
            return self.text[peek_pos]
        return None
          
    def skip_white(self):
        while self.current_char is not None and self.current_char.isspace():  # cuando el caracter actual no es NULL O VOID O no es espacio
            self.advance()

    def skip_comment(self):
        if self.current_char == '/' and self.peek() == '/':
            self.advance()  #Avanza el primer /
            self.advance()  #Avanza el segundo /
            while self.current_char is not None and self.current_char != '\n':
                self.advance()
            return True
        return False

    def Num(self):  # no confundir con NUM del enum, esta es solo una funcion
        result = '' 
        start_ln = self.Ln
        start_col = self.Col
        
        # inicio del manejo de enteros
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        #parte decimal     
        if self.current_char == '.':
            result += self.current_char
            self.advance()
            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()  
                
        return Token(token_Type.NUM, result, start_ln, start_col)
    
    def STR(self): # Para strings normales "..."
        result = ''
        start_ln = self.Ln
        start_col = self.Col
        self.advance() # consume la primera comilla "
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\\': # Manejo de secuencias de escape simples
                self.advance()
                if self.current_char is None: # Fin de archivo inesperado
                    raise Exception(f"LEXER_EXCEPTION: End Of Line not found {start_ln}:{start_col}")
                if self.current_char == 'n': result += '\n'
                elif self.current_char == 't': result += '\t'
                elif self.current_char == '"': result += '"'
                elif self.current_char == '\\': result += '\\'
                else: result += '\\' + self.current_char # Mantener la barra si no es un escape conocido
            else:
                result += self.current_char
            self.advance()

        if self.current_char != '"':
            raise Exception(f"LEXER_EXCEPTION: cadena normal no cerrada en posicion {start_ln}:{start_col}")
        self.advance()  # para avanzar la comilla de cierre "

        return Token(token_Type.STRING, result, start_ln, start_col)
    
    def f_STRING(self, start_ln_f: int, start_col_f: int):
        self.advance()  
        result=''
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        if self.current_char != '"':
            raise Exception(f"LEXER_EXCEPTION: cadena f-string no cerrada en POS {start_ln_f}:{start_col_f}")
        self.advance()  # Avanza la comilla de cierre "
        return Token(token_Type.TOK_F_STRING, result, start_ln_f, start_col_f)



    def IDENTIFIER(self):
        result = ''
        start_ln = self.Ln
        start_col = self.Col
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        token_type = self.keywords.get(result, token_Type.IDENTIFIER)  # si no es una palabra clave, se considera un IDENTIFIER
        return Token(token_type, result, start_ln, start_col)  # retorna el token
        
    def get_next_tok(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_white()  
                if self.current_char is None:
                    break  
                continue

            if self.current_char=='/' and self.peek() == '/': #comentarios
                if self.skip_comment():
                    if self.current_char is None:
                        break
                    continue
            if self.current_char == 'f' and self.peek() == '"':  # f-string
                start_ln_f_val = self.Ln
                start_col_f_val = self.Col
                self.advance() 
                return self.f_STRING(start_ln_f_val, start_col_f_val)
            

            if self.current_char.isalpha() or self.current_char == '_':#si no es comentario es un literal o variable
                return self.IDENTIFIER()
            
            if self.current_char == '"':
                return self.STR()
            
            if self.current_char.isdigit():
                return self.Num()
            
            if self.current_char=='/'and self.peek() != '/':
                token=Token(token_Type.TOK_DIV,'/',self.Ln,self.Col)#implementacion para la division teniendo en cuenta que
                #los comentarios al igual que las divisiones usan /
                tok=Token(token_Type.TOK_DIV,'/',self.Ln,self.Col)
                self.advance()
                return tok
            
            single_char_TOK={
                '=': token_Type.TOK_EQUAL, 
                '{': token_Type.TOK_LEFT_BRACE,
                '}': token_Type.TOK_RIGHT_BRACE, 
                '+': token_Type.TOK_PLUS,
                '-': token_Type.TOK_MINUS, 
                '*': token_Type.TOK_MULT,
                '(': token_Type.TOK_LEFT_PAREN, 
                ')': token_Type.TOK_RIGHT_PAREN,
                ';': token_Type.TOK_SEMICOMMA, 
                ',': token_Type.TOK_COMMA
            }
            if self.current_char in single_char_TOK:
                token_Type_val=single_char_TOK[self.current_char]
                char_value=self.current_char
                start_Ln=self.Ln
                start_Col=self.Col
                self.advance()
                return Token(token_Type_val,char_value,start_Ln,start_Col)

            
            raise Exception(f"caracter desconocido/no integrado: '{self.current_char}' en linea:{self.Ln} columna:{self.Col}")
            
        return Token(token_Type.EOF, '', self.Ln, self.Col)
        
    def tokenize(self):
        tokens_raw_list = []
        while True:
            token = self.get_next_tok()  
            tokens_raw_list.append(token)
            if token.type == token_Type.EOF:
                break
                
       
        tokens_procesadosList:list[Token] = []
        i = 0
        #multiplicacion implicita
        while i < len(tokens_raw_list):
            current = tokens_raw_list[i]
            tokens_procesadosList.append(current)

            if current.type==token_Type.EOF:
                break

            if i + 1 < len(tokens_raw_list):
                next_token = tokens_raw_list[i + 1]
                if next_token.type!=token_Type.EOF:
                    is_current_factor_end = current.type in (token_Type.NUM, token_Type.IDENTIFIER, token_Type.TOK_RIGHT_PAREN)
                if is_current_factor_end and next_token.type == token_Type.TOK_LEFT_PAREN:  
                    col_mult=current.col+len(str(current.value))
                    mult_token=Token(token_Type.TOK_MULT,'*',current.ln,col_mult)
                    tokens_procesadosList.append(mult_token)
                    #Multiplicación implícita end         
            i += 1

        if not tokens_procesadosList or tokens_procesadosList[-1].type != token_Type.EOF:
            eof_token_to_add = Token(token_Type.EOF, '', self.Ln, self.Col)
            if tokens_raw_list and tokens_raw_list[-1].type==token_Type.EOF:
                eof_token_to_add=tokens_raw_list[-1]
            if not tokens_procesadosList or tokens_procesadosList[-1].type != token_Type.EOF:
                tokens_procesadosList.append(eof_token_to_add)
        return tokens_procesadosList
