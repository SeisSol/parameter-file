#!/usr/bin/env python3

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