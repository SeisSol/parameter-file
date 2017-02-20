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

from lexer import FortranLexer
from yacc import FortranYacc

def generateParameterFile(filename, namelists):
	nodefault = 0
	
	f = open(filename, 'w')
	
	for namelist in namelists:
		f.write('!-----------------------------\n')
		f.write('&%s\n' % namelist.name())
		f.write('!-----------------------------\n')
		
		for parameter in namelist.parameters():
			f.write('\n')
			
			define = parameter.define()
			type = define.type()
			
			if define.annotation():
				f.write('%s\n' % define.annotation().format())

			if type.type() == 'character' and type.hasLength():
				f.write('! Max length: %d\n' % type.length)
			
			if type.hasDimension():
				if type.dimension == 'inf':
					f.write('! WARNING: Dimension set at runtime\n')
				else:
					f.write('! Dimension size: %d\n', type.dimension)
			
			if not parameter.hasValues():
				f.write('! WARNING: Default value not found\n')
				nodefault += 1
			else:
				if not parameter.hasAllValues():
					f.write('! WARNING: Not all default values set in array\n')
				if not parameter.hasCorrectValueType():
					f.write('! ERROR: Invalid convertion for default value to %s\n' % type.type())
				
			values = ' '.join(map(str, parameter.values()))
			f.write('%s = %s\n' % (parameter.name(), values))
			
		f.write('/\n\n')
	
	f.close()
	
	if nodefault > 0:
		print("Found %d parameters without a default value" % nodefault)
	
if __name__ == '__main__':
	lexer = FortranLexer()
	yacc = FortranYacc(lexer.tokens())
	
	f = open('../SeisSol/src/Reader/readpar.f90')
	if False:
	#if True:
		lexer.lexer().input(f.read())
		while True:
			tok = lexer.lexer().token()
			if not tok:
				break;
			print(tok)
	else:
		yacc.parse(f.read(), lexer)
	f.close()
	
	generateParameterFile('parameters.par', yacc.namelists())
	
	if (lexer.hasError()):
		sys.exit(1)
	if (yacc.hasError()):
		sys.exit(2)