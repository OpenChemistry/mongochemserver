from pyparsing import *
import string
import re

#
# This module contains a parser for a simple query language that can encode
# in value of a URL query parameter without the need to encode any characters.
#
# There are six comparison operators:
#
#   ~eq~   - string or numeric equals in the case of string equals * can be used
#           as a wildcard.
#   ~ne~   - string or numeric not equals.
#   ~gt~   - numeric greater than, has not meaning for strings.
#   ~gte~  - numeric greater or equal than, has not meaning for strings.
#   ~lt~   - numeric less than, has not meaning for strings.
#   ~lte~  - numeric less or equal than, has not meaning for strings.
#   ~slr~  - similarity search based on smile
#
# The comparison operators can be using with the follow string fields:
#   inchi
#   inchikey
#   name
#   formula
#   smiles
#
# or the following numeric fields:
#
#   mass
#   atomCount
#
# The comparison operators can be combine using the following two boolean
# operator, precedence is left to right:
#
#   ~or~   - logical OR
#   ~and~  = logical AND
#
# Example:
#
#   mass~eq~100   - Find all molecules with a mass of 100
#   mass~eq~100~and~atomCount~gt~3 - Find all molecules with a mass of 100 and
#   an atomCount of greater than 3.
#
#

# Define the supported operators
EQ = '~eq~'
NE = '~ne~'
GT = '~gt~'
GTE = '~gte~'
LT = '~lt~'
LTE = '~lte~'
OR = '~or~'
AND = '~and~'
SIMILAR = '~slr~'

# The root of the operator hierarchy
class Operator(object):
    def __init__(self, t):
        self.args = t[0][::2]
        self.op = t[0][1]

    def query(self):
        pass

class Similar(Operator):
    def query(self):
        return 'similarity?q=%s' % self.args[1]

# basic comparison
class Comparison(Operator):
    _op_map = {
        GT : '$gt',
        GTE : '$gte',
        LT : '$lt',
        LTE : '$lte',
        NE : '$ne'
    }

    def query(self):
        q = dict()
        q[self.args[0]] = {self._op_map[self.op]: self.args[1]}

        return q

# numeric equals
class NumericEquals(Comparison):
  def query(self):
    return {self.args[0]: self.args[1]}

# string equals
class StringEquals(Comparison):
    def query(self):
        value = self.args[1]

        #if self.args[0] == 'inchi':
        #    value = value.replace('InChI=', '')

        if '*' in value:
            value = value.replace('*', '.*')
            value = value.replace('(', '\(')
            value = value.replace('[', '\[')
            value = value.replace('+', '\+')
            value = re.compile('^%s$' % value)

        return {self.args[0]: value}

# boolean operators
class BooleanOp(Operator):
    _op_map = {
        AND: '$and',
        OR: '$or'
    }

    def query(self):
        q = dict()

        op_args = []
        for arg in self.args:
            op_args.append(arg.query())

        q[self._op_map[self.op]] = op_args

        return q


class And(BooleanOp):
    def query(self):
        q = dict()

        and_args = []
        for arg in self.args:
            and_args.append(arg.query())

        q['$and'] = and_args

        return q

class Or(BooleanOp):
    def query(self):
        q = dict()

        or_args = []

        for arg in self.args:
            or_args.append(arg.query())

        q['$or'] = or_args

        return q

# Define the syntax of the query language
integer = Word(nums).setParseAction(lambda t: int(t[0]))
real = Combine(Word(nums) + "." + Word(nums)).setParseAction(lambda t: float(t[0]))
numeric_field = oneOf('mass atomCount')
string_field = oneOf('name formula inchi inchikey smiles')
smiles_field = oneOf('smiles')
string = Word(string.ascii_letters+string.digits+'=/-+*[](), .')
comparision = oneOf([EQ, NE, GT, GTE, LT, LTE])
boolean = oneOf([AND, OR])
comparison_operand = real | integer | numeric_field
comparison_string_operand = string_field | string


numeric_comparison = operatorPrecedence(comparison_operand,
                                [(GT, 2, opAssoc.LEFT, Comparison),
                                 (GTE, 2, opAssoc.LEFT, Comparison),
                                 (LT, 2, opAssoc.LEFT, Comparison),
                                 (LTE, 2, opAssoc.LEFT, Comparison),
                                 (NE, 2, opAssoc.LEFT, Comparison),
                                 (EQ, 2, opAssoc.LEFT, NumericEquals)]
                                )

string_comparison = operatorPrecedence(comparison_string_operand,
                                       [(EQ, 2, opAssoc.LEFT, StringEquals),
                                        (NE, 2, opAssoc.LEFT, Comparison)]
                                       )

comparison =  numeric_comparison | string_comparison

boolean_expression = operatorPrecedence(comparison,
                           [(AND, 2, opAssoc.LEFT, BooleanOp),
                            (OR, 2, opAssoc.LEFT, BooleanOp)]
                          )
similar_operand = smiles_field | string
similar_expression = operatorPrecedence(similar_operand, [(SIMILAR, 2, opAssoc.LEFT, Similar)])

class InvalidQuery(Exception):
    def __init__(self, query):
        self.query = query

    def __str__(self, *args, **kwargs):
        return "Invalid query: %s" % self.query

def _replace_key(d, key, new_key):
    for k, v in d.items():
        if isinstance(v, dict):
            _replace_key(v, key, new_key)
        elif isinstance(v, list):
            for i in v:
                _replace_key(i, key, new_key)

        if k == key:
            d[new_key] = v
            del d[key]

    return d

# Map query key to mongodb properties
_key_map = {
        'mass': 'properties.mass',
        'atomCount': 'properties.atomCount',
        'formula': 'properties.formula'
}

# main function used by external modules to convert query into dict that can
# be used with pymongo find function.
def to_mongo_query(query):

    try:
        result = boolean_expression.parseString(query, parseAll=True)
    except ParseException:
        raise InvalidQuery(query)

    if len(result) != 1:
        raise InvalidQuery(query)

    if not isinstance(result[0], Operator):
        raise InvalidQuery(query)

    q = result[0].query()

    for (key, value) in _key_map.items():
        print(key)
        _replace_key(q, key, value)

    print(q)

    return q
