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

import sys

import ply.yacc as yacc

from namelist import Namelist, Parameter, Define, Type

class ParseError(Exception):
	pass
	
class Defines(dict):
	pass

class Assigns(dict):
	pass

class FortranYacc:
	# Enable/Disable debug information
	__debug = False
	
	# Has error
	__hasError = False
	
	# The namelists found in the file
	__namelists = []
	
	def __init__(self, tokens):
		# Currently node needed
		#precedence = ()

		def p_file_lines(p):
			# First rule reads empty lines
			'''file_lines : END_LINE file_lines
				| file_statement
				| file_statement END_LINE
				| file_statement END_LINE file_lines'''
			
		def p_file_statement_error(p):
			'file_statement : error'

		def p_file_statement_module(p):
			'''file_statement : MODULE ID END_LINE module_lines module_end
				| MODULE ID END_LINE module_end'''
			#print('module %s' % p[2])
			
		def p_module_end(p):
			'''module_end : ENDMODULE
				| ENDMODULE ID'''
				
		def p_module_lines(p):
			# First rule read empty lines
			'''module_lines : END_LINE module_lines
				| module_statement
				| module_statement END_LINE
				| module_statement END_LINE module_lines'''
				
		def p_module_statement_error(p):
			'module_statement : error'
			self.__testForImportantToken(p[1])
			#print('module error', p[1])
			#print("Parser state: %s" % self.__parser.statestack)
			#print("Parse symstack: %s" % self.__parser.symstack)
			
		def p_module_statement_subroutine(p):
			'''module_statement : SUBROUTINE ID BRACKET func_parameter BRACKET subroutine_bind subroutine_lines end_subroutine'''
			#print(p[2])
			
			defines = Defines()
			assigns = Assigns()
			namelists = []
			
			for line in p[7]:
				if not line:
					continue
				
				if type(line) is Defines:
					if namelists:
						ParseError("Found define after namelist in '%s'" % p[2])
					if assigns:
						ParseError("Found define after assigns in '%s'" % p[2])
					defines.update(line)
				elif type(line) is Namelist:
					if assigns:
						ParseError("Found namelist after assigns in '%s'" % p[2])
					namelists.append(line)
				elif type(line) is Assigns:
					for id, value in line.items():
						if not id in assigns:
							assigns[id] = []
						assigns[id].extend(value)
					
			for namelist in namelists:
				for parameter in namelist.parameters():
					if not parameter.lname() in defines:
						raise ParseError("Parameter '%s' in namelist '%s' not defined" % (parameter.name(), namelist.name()))
						
					parameter.setDefine(defines[parameter.lname()])
					if parameter.lname() in assigns:
						parameter.setValues(assigns[parameter.lname()])
					# TODO add comment
					
			self.__namelists.extend(namelists)
			
		def p_func_parameter(p):
			'''func_parameter :
				| ID
				| ID COMMA func_parameter'''
			if len(p) == 2:
				p[0] = [p[1]]
			elif len(p) == 4:
				p[0] = [p[1]] + p[3]
			else:
				p[0] = []
			
		def p_subroutine_bind(p):
			'''subroutine_bind :
				| BIND BRACKET error BRACKET'''
			
		def p_end_subroutine(p):
			'''end_subroutine : ENDSUBROUTINE
				| ENDSUBROUTINE ID'''
			
		def p_subroutine_lines_empty(p):
			'subroutine_lines : empty_statement'
			p[0] = []
			
		def p_subroutine_lines_statements(p):
			'subroutine_lines : END_LINE subroutine_statements'
			p[0] = p[2]
				
		def p_empty_statement(p):
			'''empty_statement : END_LINE
				| END_LINE empty_statement'''
				
		def p_subroutine_lines(p):
			'''subroutine_statements : subroutine_statement
				| subroutine_statement END_LINE
				| subroutine_statement END_LINE subroutine_statements'''
			p[0] = [p[1]]
			if len(p) > 3:
				p[0] += p[3]
				
		def p_subroutine_error(p):
			'subroutine_statement : error'
			self.__testForImportantToken(p[1])
			#print('subroutine error', p[1])
			
		def p_subroutine_statement_definition(p):
			'subroutine_statement : type_definition DEFINE define_variables'
			p[0] = Defines()
			for param,size in p[3]:
				param = param.lower()
				define = Define(p[1])
				define.setSize(size)
				p[0][param] = define
					
		def p_type_definition(p):
			'''type_definition : type
				| type COMMA type_modifer_list'''
			p[0] = p[1]
			if len(p) > 2:
				for attr, value in p[3].items():
					setattr(p[0], attr, value)
				
		def p_type(p):
			'''type : REAL
				| INTEGER
				| CHARACTER
				| CHARACTER BRACKET INT BRACKET
				| CHARACTER BRACKET ID ASSIGN INT BRACKET'''
			type = Type(p[1])
			if len(p) > 2:
				if len(p) > 5:
					if p[3].lower() != 'len':
						raise ParseError('Unknown type modifier %s' % p[3])
					type.length = p[5]
				else:
					type.length = p[3]
			p[0] = type
				
		def p_type_modifier_list(p):
			'''type_modifer_list : type_modifier
				| type_modifer_list COMMA type_modifier'''
			p[0] = p[1]
			if len(p) > 2:
				p[0].update(p[3])
				
		def p_type_modifier(p):
			'''type_modifier : DIMENSION BRACKET RANGE BRACKET
				| ALLOCATABLE'''
			if len(p) == 5:
				p[0] = {'dimension': 'inf'}
			else:
				p[0] = {}
				
		def p_define_variables(p):
			'''define_variables : define_variable
				| define_variable COMMA define_variables'''
			if len(p) == 2:
				p[0] = [p[1]]
			elif len(p) == 4:
				p[0] = [p[1]] + p[3]
			else:
				p[0] = []
				
		def p_define_variable(p):
			'''define_variable : ID
				| ID BRACKET INT BRACKET
				| ID BRACKET INT RANGE INT BRACKET '''
			if len(p) == 5:
				size = p[3]
			elif len(p) == 7:
				if p[3] != 1:
					print("WARNING: Define range not starting from 1 in line %d\n\tThis leads to incorrect default values." % p.lineno(3))
				size = p[5] - p[3] + 1
			else:
				size = 1
			p[0] = (p[1], size)

		def p_subroutine_statement_namelist(p):
			'subroutine_statement : NAMELIST SLASH ID SLASH namelist_variables'
			p[0] = Namelist(p[3], p[5])
			
		def p_namelist_variables(p):
			'''namelist_variables : ID
				| ID COMMA namelist_variables'''
			p[0] = [Parameter(p[1])]
			if len(p) > 2:
				p[0] += p[3]
				
		def p_subroutine_statement_assign(p):
			'subroutine_statement : ID ASSIGN expression'
			p[0] = Assigns()
			p[0][p[1].lower()] = [(p[3], 0, sys.maxsize)]
			
		def p_subroutine_statement_arrayassign(p):
			'subroutine_statement : ID BRACKET RANGE BRACKET ASSIGN expression'
			p[0] = Assigns()
			p[0][p[1].lower()] = [(p[6], 0, sys.maxsize)]
			
		def p_subroutine_statement_partialarrayassign(p):
			'subroutine_statement : ID BRACKET INT RANGE INT BRACKET ASSIGN expression'
			p[0] = Assigns()
			p[0][p[1].lower()] = [(p[8], p[3]-1, p[5])]
		
		def p_expression(p):
			'''expression : INT
				| FLOAT
				| LITERAL'''
			p[0] = p[1]
				
		#def p_subroutine_statement_if(p):
			#'''subroutine_statement : IF error THEN subroutine_lines ENDIF
				#| IF error THEN subroutine_lines END IF'''
				
		#def p_subroutine_statement_do(p):
			#'''subroutine_statement : DO error END_LINE subroutine_statements ENDDO'''
				 #| DO error END_LINE subroutine_statements END DO'''
				 
		#def p_subroutine_statement_select(p):
			#'''subroutine_statement : SELECT CASE BRACKET error BRACKET subroutine_lines ENDSELECT
				#| SELECT CASE BRACKET error BRACKET subroutine_lines END SELECT'''

		def p_error(p):
			if not p:
				print('Invalid parser state reached')
				if self.__debug:
					print("Parser stack: %s" % self.__parser.statestack)
				self.__hasError = True
			elif self.__debug:
				print("Syntax error at line %d '%s'" % (p.lineno, p.value))
			#self.__parser.errok()
			
		
		self.__parser = yacc.yacc(debug=self.__debug)
		
	def parse(self, text, lexer):
		self.__parser.parse(text, lexer=lexer.lexer())
		
	def namelists(self):
		return self.__namelists
	
	def hasError(self):
		return self.__hasError
	
	def __testForImportantToken(self, token):
		if token.type == 'SUBROUTINE':
			print('Skipping subroutine at line %d' % token.lineno, file=sys.stderr)
			#print("Parser stack: %s" % self.__parser.statestack)
			self.__hasError = True
		elif token.type == 'NAMELIST':
			print('Skipping namelist at line %d' % token.lineno, file=sys.stderr)
			self.__hasError = True