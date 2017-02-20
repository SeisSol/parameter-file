#!/usr/bin/env python3
##
# @file
# This file is part of SeisSol.
#
# @author Sebastian Rettenberger (sebastian.rettenberger AT tum.de, http://www5.in.tum.de/wiki/index.php/Sebastian_Rettenberger)
#
# @section LICENSE
# Copyright (c) 2017, SeisSol Group
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# @section DESCRIPTION
#

import collections
import sys

import ply.lex as lex

class LexError(Exception):
	pass

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
	
	__reserved_annotation = {
		'allowed_values' : 'ANNO_ALLOWED_VALUES',
		'warning' : 'ANNO_WARNING',
		'more_info' : 'ANNO_MORE_INFO'
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
		'ID',
		'ANNO_START',
		'ANNO_CONTINUE',
		'ANNO_KEYWORD',
		'ANNO_TEXT'
	] + list(__reserved.values()) + list(__reserved_annotation.values())
	
	__hasError = False
	
	def __init__(self):
		tokens = self.__ignore_tokens + self.__tokens
		
		states = (
			('annotation', 'exclusive'),
		)

		def t_PREPROCESSOR(t):
			r'\#.*\n'
			t.lexer.lineno += 1

		def t_COMMENT(t):
			# Matches only non-annotation comments
			r'!([^!>\n][^\n]*|)\n'
			t.lexer.lineno += 1
			t.type = 'END_LINE'
			return t

		t_ignore_SPACE = r'[\ \t]+'
		def t_ignore_LINE_BREAK(t):
			# Annotation comments after a line break is
			# currently not supported. Might not make
			# sense anyway.
			r'&\ *(![^\n]*)?\n'
			t.lexer.lineno += 1

		def t_ANY_END_LINE(t):
			r'\n+'
			t.lexer.lineno += len(t.value)
			t.lexer.begin('INITIAL')
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
		
		def t_ANNO_START(t):
			r'!>\ *'
			t.lexer.begin('annotation')
			return t
		
		def t_ANNO_CONTINUE(t):
			r'!!\ *'
			t.lexer.begin('annotation')
			return t
		
		def t_annotation_ANNO_KEYWORD(t):
			r'@[a-z_]+'
			t.value = t.value[1:]
			tlower = t.value.lower()
			if not tlower in self.__reserved_annotation:
				# Might be an annotation outside of a subroutine
				print("WARNING: Unknown anntation keyword '%s' in line %d" % (t.value, t.lexer.lineno), file=sys.stderr)
				#raise LexError("Unknown annotation keyword '%s' in line %d" % (t.value, t.lexer.lineno))
				pass
			else:
				t.type = self.__reserved_annotation.get(tlower)
			return t
		
		def t_annotation_ANNO_TEXT(t):
			r'[^\n]+'
			t.value = t.value.strip()
			return t

		def t_ANY_error(t):
			print("Illegal character '%s'" % t.value[0], file=sys.stderr)
			t.lexer.skip(1)
			self.__hasError = True
			
		mergeTokens = {'END' : {'MODULE', 'SUBROUTINE'}} #, 'IF', 'DO', 'SELECT'}}
			
		self.__lexer = MergeLexer(lex.lex(), mergeTokens)
		self.__tokens = list(set(self.__tokens + self.__lexer.virtualTokens)) # Add virtual tokens from the merger
		self.__tokens = [t for t in self.__tokens if not t in {'END', 'ANNO_KEYWORD'}] # Not interesting for yacc
		
	def lexer(self):
		return self.__lexer
	
	def tokens(self):
		return self.__tokens
		
	def hasError(self):
		return self.__hasError