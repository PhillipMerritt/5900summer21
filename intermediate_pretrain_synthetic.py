"""
<statement> → <expr><compare><expr>

<expr> → <select> when <where> |
        <select>

<select> → <column> |
        the <aggr> of <column> |
        the count

<where> → <column><compare><value> |
        <where> and <where>

<aggr> → first | last |
        lowest | greatest |
        sum | average | range

<compare> → is |
            is greater than |
            is less than

<value> → <string> | <number>

notes:
<select> values are constrained to be either both "the count" or to have the same value for <column>
P(<select> → the count): 0.2 

<columns> is the set of column names in the table

<aggr>:
Name        Result
first       the value in C with the lowest row index.
last        the value in C with the highest row index.
greatest    the value in C with the highest numeric value.
lowest      the value in C with the lowest numeric value.
sum         The sum of all the numeric values.
average     The average of all the numeric values.
range       The difference between greatest and lowest.

C are the column values. Fails when C is empty or there are non-numeric values

<value> is chosen at random from the respective column

With probability 0.5 we replace one of both expressions by the values it evaluates to.
"""
from csv import Sniffer
import random
import numpy as np

class SynthException(BaseException):
    pass

class Is_Compare():
    def eval(self, a, b):
        if type(a) == np.ndarray or type(b) == np.ndarray or type(a) == list or type(b) == list:
            print(a, b)
        return a == b
    def __str__(self):
        return 'is'

class IsGreaterThan_Compare():
    def eval(self, a, b):
        """ if type(a) == np.ndarray or type(a) == np.ndarray:
            print(a, b) """
        try:
            min_a = min(a)
        except:
            min_a = a
        try:
            max_b = max(b)
        except:
            max_b = b
        return min_a > max_b
    def __str__(self):
        return 'is greater than'

class IsLessThan_Compare():
    def eval(self, a, b):
        """ if type(a) == np.ndarray or type(a) == np.ndarray:
            print(a, b) """
        try:
            min_b = min(b)
        except:
            min_b = b
        try:
            max_a = max(a)
        except:
            max_a = a
        return max_a < min_b
    def __str__(self):
        return 'is less than'

STATEMENT_ATTEMPTS = 50
compare_choices = [Is_Compare, IsGreaterThan_Compare, IsLessThan_Compare]

class CFG():
    def __init__(self, result, table):
        self.result = result
        self.table = table
        #self.expr_choices = {0: lambda self: '{} when {}'.format(self.select(), self.where()), 1: lambda self: self.select()}
        #self.where_choices = {0: lambda self: '{} {} {}'.format(self.column(), self.compare(), self.value()), 1: lambda self: '{} and {}'.format()}
        self.aggr_choices = {0: 'first', 1: 'last', 2: 'lowest', 3: 'greatest', 4: 'sum', 5: 'average', 6: 'range'}
        self.expression_a = None
        self.expression_b = None
        self.compares = [Is_Compare(), IsGreaterThan_Compare(), IsLessThan_Compare()]

    def get_statement(self):
        for _ in range(STATEMENT_ATTEMPTS):
            try:
                self.expr() # create both expressions
                comparisons = self.compare()
                a, b = self.expression_a.evaluate(), self.expression_b.evaluate()
            except SynthException as e:
                #print(e)
                continue

            for comparison in comparisons:
                #print(type(a), type(b))
                #print(a, b)
                if type(a) == list:
                    a = set(a)
                if type(b) == list:
                    b = set(b)

                if comparison.eval(a, b) == self.result:
                    num = random.randint(0,1)
                    if num == 0:    # replace one of the expressions with what it evaluates to
                        if type(a) == set:#list:
                            a = random.choice(list(a))
                        return '{} {} {}'.format(a, comparison, self.expression_b)
                    if type(b) == set:#list:
                        b = random.choice(list(b))
                    return '{} {} {}'.format(self.expression_a, comparison, b)
        return None


    def expr(self):
        """
            Get both selections.
        """
        # find type for first select
        num = random.random()
        agg = None
        column = None
        if num <= 0.4:
            column =  self.table.random_numeric_column()#self.column()
        elif num <= 0.8:
            column =  self.table.random_numeric_column()
            agg = self.aggr(column)
        
        num = random.randint(0,1)
        # get first expression
        if num == 0: # include 'when <where>'
            self.expression_a = Expression(self.table, column, agg, when=True)
        else:
            self.expression_a = Expression(self.table, column, agg, when=False)
        
        # if the previous select wasn't 'the count' find out if this one has an aggr
        if column: 
            num = random.random()
            agg = None
            if num >= 0.5:
                agg = self.aggr(column)
        
        num = random.randint(0,1)
        if num == 0: # include 'when <where>'
            self.expression_b = Expression(self.table, column, agg, when=True)
        else:
            self.expression_b = Expression(self.table, column, agg, when=False)
    def aggr(self, column):
        num = random.randint(0,6)
        return Aggregate(self.aggr_choices[num], column, self.table) #TODO: stuff
    def compare(self):
        random.shuffle(self.compares)
        return self.compares
    def column(self):
        return random.choice(self.table.columns)

class Expression():
    def __init__(self, table, column, aggr, when):
        self.table = table
        self.column = column
        self.aggr = aggr
        self.wheres = []
        #if column and when:  # get wheres
        seen = set()
        attempts = 0
        while not self.wheres or random.random() <= 0.5:
            if len(table.numeric_columns) == 0:
                num = 0
            else:
                num = random.randint(0,2)
            comp = compare_choices[num]()
            if num == 0:
                where_col = table.random_column()
            else:
                where_col = table.random_numeric_column()

            where_value = table.random_value(where_col)
            col_idx = table.get_column_index(where_col)
            attempts = 0
            while (num, col_idx) in seen and attempts < 50:
                if len(table.numeric_columns) == 0:
                    num = 0
                else:
                    num = random.randint(0,2)
                comp = compare_choices[num]()
                if num == 0:
                    where_col = table.random_column()
                else:
                    where_col = table.random_numeric_column()
                #print(where_col, table.columns)
                where_value = table.random_value(where_col)
                col_idx = table.get_column_index(where_col)
                attempts += 1
            
            if attempts == 50:
                break

            seen.add((num, col_idx))
            self.wheres.append(Where(where_col, col_idx, where_value, comp))
        
        if not self.wheres:
            raise SynthException('Cant get where')

    def evaluate(self):
        #values = self.table.get_values(self.column)
        rows = self.table.get_rows()
        for where in self.wheres:
            rows = where.filter(rows)
        if len(rows) == 0:
            raise SynthException('failed wheres')
        col_idx = self.table.get_column_index(self.column)
        values = [row[col_idx] for row in rows]

        if self.column: # normal select or with aggr
            if self.aggr:
                temp = self.aggr.evaluate(values)
                return temp
            return values

        else: # the count
            return len(values)
    
    def __str__(self):
        if self.column: # normal select or with aggr
            if self.aggr:
                string = str(self.aggr)
            else:
                string = self.column
            
            if self.wheres:
                return string + ' when ' + ' and '.join(map(str, self.wheres))
            return string        
        # the count
        return 'the count when ' + ' and '.join(map(str, self.wheres))

class CountSelect():
    def __init__(self, rows):
        self.value = len(rows)
    def evaluate(self):
        return self.value
    def __str__(self):
        return 'the count'


class Where():
    def __init__(self, column, col_idx, value, comparison):
        self.column = column
        self.col_idx = col_idx
        self.value = value
        self.comparison = comparison

        if type(value) == list or type(value) == np.ndarray:
            print('bad where: {}'.format(value))

    def filter(self, rows):
        return [row for row in rows if self.comparison.eval(row[self.col_idx], self.value)]
    def __str__(self):
        return '{} {} {}'.format(self.column, self.comparison, self.value)

class Aggregate():
    def __init__(self, aggr_type, column, table):
        self.aggr_type = aggr_type
        self.column = column
        self.table = table
        self.is_numeric = self.table.is_numeric(column)
    def evaluate(self, values):
        if len(values) < 2:
            raise SynthException('aggregate empty list')

        if self.aggr_type == 'first':
            return values[0]
        if self.aggr_type == 'last':
            return values[-1]
        
        if not self.is_numeric:
            raise SynthException('Wrong value type')

        if self.aggr_type == 'lowest':
            num = format_number(np.min(values))
        elif self.aggr_type == 'greatest':
            num = format_number(np.max(values))
        elif self.aggr_type == 'sum':
            num = format_number(np.sum(values))
        elif self.aggr_type == 'average':
            num = format_number(np.mean(values))
        elif self.aggr_type == 'range':
            num = format_number(np.ptp(values))
        
        if type(num) == list or type(num) == np.ndarray:
            return num[0]
        return num

    def __str__(self):
        return 'the {} of {}'.format(self.aggr_type, self.column)

def format_number(num):
    num = float(num)
    if num.is_integer():
        return int(num)
    return float('{:.2f}'.format(num))

