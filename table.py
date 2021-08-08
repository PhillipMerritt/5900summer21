import csv
import pandas as pd
import random

from functools import partial

class Table():
    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows
        self.df = pd.DataFrame(data=rows, columns=columns)
        self.numeric_columns = set()

        for row in rows:
            for x in row:
                if type(x) == list:
                    print(rows)
                    raise Exception

        is_numeric = self.df.apply(lambda s: pd.to_numeric(s, errors='coerce').notnull().all())
        for numeric, col in zip(is_numeric, columns):
            if numeric:
                self.numeric_columns.add(col)
                #self.df[col] = self.df[col].map(lambda a: pd.to_numeric(a, errors='ignore'))
        
        convert = partial(pd.to_numeric, errors='ignore')
        self.df = self.df.applymap(convert)
    def random_value(self, column):
        sample = self.df[column].sample(n=1).values
        if len(sample.shape) > 1:
            return sample[0, 0]
        return sample[0]
    def random_column(self):
        return random.choice(self.df.columns)
    def random_numeric_column(self):
        if len(self.numeric_columns) == 0:
            return None
        return random.choice(list(self.numeric_columns))
    def get_values(self, column):
        return self.df[column].values
    def is_numeric(self, column):
        return column in self.numeric_columns
    def get_column_index(self, column):
        for i, col in enumerate(self.columns):
            if col == column:
                return i
    def get_rows(self):
        return self.df.values
    

def load_table(path):
    with open(path, 'r') as file:
        rows = list(csv.reader(file))
        columns, rows = rows[0], rows[1:]
        return Table(columns, rows)