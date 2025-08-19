from enum import Enum
from dataclasses import dataclass

class TokenType(Enum):
    # Special Tokens
    ILLEGAL = "ILLEGAL"
    EOF = "EOF"

    # Identifiers + Literals
    IDENT = "IDENT"
    INT = "INT"
    FLOAT = "FLOAT"
    STRING = "STRING"
    DIMENSION = "DIMENSION" # e.g., 16px, 100%

    # Operators
    ASSIGN = "="
    PLUS = "+"
    MINUS = "-"
    BANG = "!"
    ASTERISK = "*"
    SLASH = "/"
    LT = "<"
    GT = ">"
    EQ = "=="
    NOT_EQ = "!="
    LT_EQ = "<="
    GT_EQ = ">="

    # Delimiters
    COMMA = ","
    SEMICOLON = ";"
    COLON = ":"
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"
    DOT = "."
    HASH = "#"

    # Keywords
    FUNCTION = "FUNCTION"
    LET = "LET"
    CONST = "CONST"
    VAR = "VAR"
    TRUE = "TRUE"
    FALSE = "FALSE"
    IF = "IF"
    ELSE = "ELSE"
    RETURN = "RETURN"
    WHILE = "WHILE"
    FOR = "FOR"
    SWITCH = "SWITCH"
    MODULE = "MODULE"
    USE = "USE"
    COMPONENT = "COMPONENT"
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    IMPORT = "IMPORT"
    LICENSE = "LICENSE"
    PERMISSIONS = "PERMISSIONS"
    AS = "AS"

    # Types
    TYPE_INT = "INT_TYPE"
    TYPE_FLOAT = "FLOAT_TYPE"
    TYPE_BOOL = "BOOL_TYPE"
    TYPE_STRING = "STRING_TYPE"
    TYPE_VOID = "VOID_TYPE"

@dataclass
class Token:
    token_type: TokenType
    literal: str
    line: int = 1
    column: int = 1

keywords = {
    "function": TokenType.FUNCTION, "let": TokenType.LET, "const": TokenType.CONST,
    "var": TokenType.VAR, "true": TokenType.TRUE, "false": TokenType.FALSE,
    "if": TokenType.IF, "else": TokenType.ELSE, "return": TokenType.RETURN,
    "while": TokenType.WHILE, "for": TokenType.FOR, "switch": TokenType.SWITCH,
    "module": TokenType.MODULE, "use": TokenType.USE, "component": TokenType.COMPONENT,
    "public": TokenType.PUBLIC, "private": TokenType.PRIVATE, "import": TokenType.IMPORT,
    "license": TokenType.LICENSE, "permissions": TokenType.PERMISSIONS, "as": TokenType.AS,
    "int": TokenType.TYPE_INT, "float": TokenType.TYPE_FLOAT, "bool": TokenType.TYPE_BOOL,
    "string": TokenType.TYPE_STRING, "void": TokenType.TYPE_VOID,
}

def lookup_ident(ident: str) -> TokenType:
    return keywords.get(ident, TokenType.IDENT)
