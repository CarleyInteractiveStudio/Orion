from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional

class TokenType(Enum):
    # Single-character tokens
    LEFT_PAREN = auto()     # (
    RIGHT_PAREN = auto()    # )
    LEFT_BRACE = auto()     # {
    RIGHT_BRACE = auto()    # }
    LEFT_BRACKET = auto()   # [
    RIGHT_BRACKET = auto()  # ]
    COMMA = auto()          # ,
    DOT = auto()            # .
    MINUS = auto()          # -
    PLUS = auto()           # +
    SEMICOLON = auto()      # ;
    SLASH = auto()          # /
    STAR = auto()           # *
    COLON = auto()          # :
    HASH = auto()           # #

    # One or two character tokens
    BANG = auto()           # !
    BANG_EQUAL = auto()     # !=
    EQUAL = auto()          # =
    EQUAL_EQUAL = auto()    # ==
    GREATER = auto()        # >
    GREATER_EQUAL = auto()  # >=
    LESS = auto()           # <
    LESS_EQUAL = auto()     # <=
    ARROW = auto()          # =>

    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Keywords
    AND = auto()
    AS = auto()
    BOOL = auto()
    CLASS = auto()
    COMPONENT = auto()
    CONST = auto()
    ELSE = auto()
    FALSE = auto()
    FLOAT = auto()
    FOR = auto()
    FUNCTION = auto()
    IF = auto()
    IMPORT = auto()
    INT = auto()
    LET = auto()
    LICENSE = auto()
    MODULE = auto()
    OR = auto()
    PERMISSIONS = auto()
    PRIVATE = auto()
    PUBLIC = auto()
    RETURN = auto()
    STRING_TYPE = auto()
    SUPER = auto()
    SWITCH = auto()
    THIS = auto()
    TRUE = auto()
    USE = auto()
    VAR = auto()
    VOID = auto()
    WHILE = auto()

    # End of file
    EOF = auto()


@dataclass
class Token:
    token_type: TokenType
    lexeme: str
    literal: Optional[Any]
    line: int

    def __str__(self) -> str:
        return f"Token(type={self.token_type.name}, lexeme='{self.lexeme}', literal={self.literal}, line={self.line})"

# Mapping keywords to their token types
keywords = {
    "and": TokenType.AND,
    "as": TokenType.AS,
    "bool": TokenType.BOOL,
    "class": TokenType.CLASS,
    "component": TokenType.COMPONENT,
    "const": TokenType.CONST,
    "else": TokenType.ELSE,
    "false": TokenType.FALSE,
    "float": TokenType.FLOAT,
    "for": TokenType.FOR,
    "function": TokenType.FUNCTION,
    "if": TokenType.IF,
    "import": TokenType.IMPORT,
    "int": TokenType.INT,
    "let": TokenType.LET,
    "license": TokenType.LICENSE,
    "module": TokenType.MODULE,
    "or": TokenType.OR,
    "permissions": TokenType.PERMISSIONS,
    "private": TokenType.PRIVATE,
    "public": TokenType.PUBLIC,
    "return": TokenType.RETURN,
    "string": TokenType.STRING_TYPE,
    "super": TokenType.SUPER,
    "switch": TokenType.SWITCH,
    "this": TokenType.THIS,
    "true": TokenType.TRUE,
    "use": TokenType.USE,
    "var": TokenType.VAR,
    "void": TokenType.VOID,
    "while": TokenType.WHILE,
}
