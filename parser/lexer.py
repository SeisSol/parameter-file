#!/usr/bin/env python3

import collections

import ply.lex as lex

def MergeLexer(lexer, mergeTokens = {}, mergeValue = ' '):
	'''Overrides to token function in the Lexer to merge tokens'''
	def token():
		if lexer._buffer:
			token = lexer._buffer.popleft()
		else:
			token = lexer._token()
		if not token:
			# We are probably done
			return token
		
		if token.type in mergeTokens:
			nextToken = lexer._token()
			possibleTokens = mergeTokens[token.type]
			if nextToken.type in possibleTokens:
				token.type += nextToken.type
				# WARNING: We use always use the mergeValue at the moment
				# -> could be different in the code
				token.value += mergeValue + nextToken.value
			else:
				# Could not merge
				lexer._buffer.append(nextToken)
			
		return token
	
	virtualTokens = []
	for t,l in mergeTokens.items():
		virtualTokens.extend(map(lambda x: t+x, l))
	
	lexer._buffer = collections.deque()
	lexer._token = lexer.token
	lexer.token = token
	lexer.virtualTokens = virtualTokens
	return lexer

class FortranLexer:
	
	__reserved = {
		'module' : 'MODULE',
		'subroutine' : 'SUBROUTINE',
		'bind' : 'BIND',
		#'if' : 'IF',
		#'then' : 'THEN',
		#'do' : 'DO',
		#'select' : 'SELECT',
		#'case' : 'CASE',
		'end' : 'END',
		#'endif' : 'ENDIF',
		#'enddo' : 'ENDDO',
		#'endselect' : 'ENDSELECT',
		'namelist': 'NAMELIST',
		'integer': 'INTEGER',
		'real': 'REAL',
		'character': 'CHARACTER',
		'dimension': 'DIMENSION',
		'allocatable': 'ALLOCATABLE'
	}
	
	__ignore_tokens = [
		'PREPROCESSOR',
		'COMMENT',
		'SPACE',
		'LINE_BREAK',
	]
	
	__tokens = [
		'END_LINE',
		'COMMA',
		'ASSIGN',
		'BRACKET',
		'SLASH',
		'DEFINE',
		'RANGE',
		'INT',
		'FLOAT',
		'LITERAL',
		'OTHER',
		'ID'
	] + list(__reserved.values())
	
	__hasError = False
	
	def __init__(self):
		tokens = self.__ignore_tokens + self.__tokens

		def t_PREPROCESSOR(t):
			r'\#.*\n'
			t.lexer.lineno += 1

		def t_COMMENT(t):
			r'!.*\n'
			t.lexer.lineno += 1
			t.type = 'END_LINE'
			return t

		t_ignore_SPACE = r'[\ \t]+'
		def t_ignore_LINE_BREAK(t):
			r'&\ *(![^\n]*)?\n'
			t.lexer.lineno += 1

		def t_END_LINE(t):
			r'\n+'
			t.lexer.lineno += len(t.value)
			return t

		t_COMMA = r','
		t_ASSIGN = r'='
		t_BRACKET = r'\(|\)'
		t_SLASH = r'/'
		t_DEFINE = r'::'
		t_RANGE = r':'

		def t_INT(t):
			r'\d+'
			try:
				t.value = int(t.value)
			except ValueError:
				print("Integer value too large %d", t.value)
				t.value = 0
			return t

		def t_FLOAT(t):
			r'\d*\.\d+'
			t.value = float(t.value)

		def t_LITERAL(t):
			r'(\'[^\']*\')|("[^"]*")'
			t.value = t.value[1:-1]
			return t

		t_OTHER = r'\*|\.|%|;|\+|-|(<=)'

		def t_ID(t):
			r'(?i)[a-z][a-z0-9_]*'
			tlower = t.value.lower() # convert to lower case
			if tlower in self.__reserved:
				t.type = self.__reserved.get(tlower)
			return t

		def t_error(t):
			print("Illegal character '%s'" % t.value[0], file=sys.stderr)
			t.lexer.skip(1)
			self.__hasError = True
			
		mergeTokens = {'END' : {'MODULE', 'SUBROUTINE'}} #, 'IF', 'DO', 'SELECT'}}
			
		self.__lexer = MergeLexer(lex.lex(), mergeTokens)
		self.__tokens = list(set(self.__tokens + self.__lexer.virtualTokens)) # Add virtual tokens from the merger
		self.__tokens.remove('END') # Not interesting for yacc
		
	def lexer(self):
		return self.__lexer
	
	def tokens(self):
		return self.__tokens
		
	def hasError(self):
		return self.__hasError