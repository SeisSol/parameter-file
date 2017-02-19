#!/usr/bin/env python3

import copy

class Type:
	def __init__(self, type):
		self.__type = type.lower()
		
	def type(self):
		return self.__type
		
	def hasLength(self):
		return hasattr(self, 'length')
	
	def hasDimension(self):
		return hasattr(self, 'dimension')
	
	def __str__(self):
		if self.hasLength():
			return self.__type + '(len=' + str(self.length) + ')'
		return self.__type

class Define:
	__size = 1
	
	def __init__(self, type):
		self.__type = copy.deepcopy(type)
		
	def setSize(self, size):
		self.__size = size
		
	def size(self):
		return self.__size
	
	def type(self):
		return self.__type

class Parameter:
	__valueList = None
	
	def __init__(self, name):
		self.__name = name
		
	def name(self):
		return self.__name
	
	def lname(self):
		return self.__name.lower()
	
	def setDefine(self, define):
		self.__define = define
		
	def define(self):
		return self.__define
	
	def setValues(self, values):
		self._values = values
		
	def values(self):
		self.__createValueList()
		
		t = self.__define.type().type()
		def convert(value):
			if value == None:
				if t == 'integer':
					return 0
				if t == 'real':
					return 0.0
				if t == 'character':
					return "''"
				return ''
		
			if t == 'integer':
				return int(value)
			if t == 'real':
				return float(value)
			if t == 'character':
				return "'" + str(value) + "'"
			return value
		
		return map(convert, self.__valueList)
		
	def hasValues(self):
		return hasattr(self, '_values')
	
	def hasAllValues(self):
		self.__createValueList()
		return not None in self.__valueList
	
	def hasCorrectValueType(self):
		self.__createValueList()
		
		t = self.__define.type().type()
		for value in self.__valueList:
			if t == 'integer':
				if isinstance(value, int):
					return True
				elif isinstance(value, float):
					print("Warning: Converting float expression to integer type for '%s'" % self.__name)
					return True
				return False
			if t == 'real':
				if isinstance(value, (int, float)):
					return True
				return False
			if t == 'character':
				if isinstance(value, str):
					return True
				return False
			return True
	
	def __createValueList(self):
		if self.__valueList:
			return
		
		self.__valueList = [None] * self.__define.size()
		
		if self.hasValues():
			for value,start,end  in self._values:
				for i in range(start, min(end, len(self.__valueList))):
					if self.__valueList[i] == None:
						self.__valueList[i] = value

class Namelist:
	def __init__(self, name, parameters):
		self.__name = name
		self.__parameters = parameters
		
	def name(self):
		return self.__name
	
	def parameters(self):
		return self.__parameters