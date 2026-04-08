from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Dict, List, Any

class SymbolType(Enum):
    VARIABLE = auto()
    FUNCTION = auto()
    BUILTIN = auto() 
    STRING = auto() 

@dataclass
class Symbol:
    name: str
    type: SymbolType
    scope_level: int
    
    params: Optional[List[str]] = None 
    node: Optional[Any] = None 


class SymbolTable:
    def __init__(self):
        
        self.scoped_symbols: List[Dict[str, Symbol]] = [{}] 
        self.current_scope_level = 0
        self._initialize_builtins()

    def _initialize_builtins(self):
        self.define('print', SymbolType.BUILTIN)
       
    def enter_scope(self):
        
        self.current_scope_level += 1
        self.scoped_symbols.append({})
        
    def exit_scope(self):
        """Sale del scope actual."""
        if self.current_scope_level > 0:
            self.current_scope_level -= 1
        else:
            print("Advertencia: Intento de salir del scope global.")

    def define(self, name: str, symbol_type: SymbolType, params: Optional[List[str]] = None, node: Optional[Any] = None) -> Symbol:
        """Define un nuevo símbolo en el scope actual."""
        current_scope = self.scoped_symbols[-1]
        if name in current_scope:
            
            print(f"Advertencia: Redefinición del símbolo '{name}' en el scope actual (nivel {self.current_scope_level}).")

        symbol = Symbol(name=name, type=symbol_type, scope_level=self.current_scope_level, params=params, node=node)
        current_scope[name] = symbol
        return symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        """Busca un símbolo desde el scope actual hacia afuera (global)."""
        for i in range(self.current_scope_level, -1, -1):
            scope = self.scoped_symbols[i]
            if name in scope:
                return scope[name]
        return None 

    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        """Busca un símbolo SOLO en el scope actual."""
        return self.scoped_symbols[-1].get(name)


if __name__ == "__main__":
    st = SymbolTable()
    st.define("global_var", SymbolType.VARIABLE)
    print(f"Scope Global: {st.scoped_symbols[0]}")

    st.enter_scope() 
    st.define("local_var", SymbolType.VARIABLE)
    st.define("global_var", SymbolType.VARIABLE) 

    print(f"Lookup 'local_var': {st.lookup('local_var')}")
    print(f"Lookup 'global_var': {st.lookup('global_var')} (debería ser la local)")

    print(f"Scope Actual (1): {st.scoped_symbols[-1]}")
    st.exit_scope() 

    print(f"Lookup 'local_var' (global): {st.lookup('local_var')} (debería ser None)")
    print(f"Lookup 'global_var' (global): {st.lookup('global_var')} (debería ser la global)")
    print(f"Scope Actual (0): {st.scoped_symbols[-1]}")