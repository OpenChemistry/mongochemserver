import unittest
import query
import re

#
# unit tests for query parser
#
class TestQueryParser(unittest.TestCase):

    def setUp(self):
        self.seq = range(10)

    def test_valid(self):
        queries = {'mass~gt~0~and~mass~lt~100~or~atomCount~gt~2': {'$or': [{'$and': [{'properties.mass': {'$gt': 0}},{'properties.mass': {'$lt': 100}}]}, {'properties.atomCount': {'$gt': 2}}]} ,
                'atomCount~lt~10~or~mass~lt~10~and~mass~gt~100': {'$or': [{'properties.atomCount': {'$lt': 10}}, {'$and': [{'properties.mass': {'$lt': 10}}, {'properties.mass': {'$gt': 100}}]}]},
                'mass~gt~100': {'properties.mass': {'$gt': 100}},
                'mass~gt~1~and~mass~gt~2~and~mass~gt~3': {'$and': [{'properties.mass': {'$gt': 1}}, {'properties.mass': {'$gt': 2}}, {'properties.mass': {'$gt': 3}}]} ,
                'mass~gt~1~and~mass~gt~2~and~mass~gt~3~or~mass~lt~1': {'$or': [{'$and': [{'properties.mass': {'$gt': 1}}, {'properties.mass': {'$gt': 2}}, {'properties.mass': {'$gt': 3}}]}, {'properties.mass': {'$lt': 1}}]},
                'mass~gt~10~or~mass~gt~11~or~mass~gt~12': {'$or': [{'properties.mass': {'$gt': 10}}, {'properties.mass': {'$gt': 11}}, {'properties.mass': {'$gt': 12}}]} ,
                'mass~gt~2~or~mass~gt~3': {'$or': [{'properties.mass': {'$gt': 2}}, {'properties.mass': {'$gt': 3}}]},
                'mass~lt~1~and~atomCount~gt~23~or~atomCount~lt~1~and~mass~lt~0': {'$or': [{'$and': [{'properties.mass': {'$lt': 1}}, {'properties.atomCount': {'$gt': 23}}]}, {'$and': [{'properties.atomCount': {'$lt': 1}}, {'properties.mass': {'$lt': 0}}]}]},
                'mass~ne~1': {'properties.mass': {'$ne': 1}},
                'mass~eq~1': {'properties.mass': 1},
                'mass~eq~3.14159': {'properties.mass': 3.14159},
                'atomCount~eq~3.14159': {'properties.atomCount': 3.14159},
                'inchi~eq~CH': {'inchi': 'CH'},
                'inchi~eq~CH*': {'inchi': re.compile('^CH.*$')},
                'inchi~ne~CH': {'inchi': {'$ne': 'CH'}},
                'inchi~ne~CH*': {'inchi': {'$ne': 'CH*'}},
                'name~eq~test test~and~mass~gt~1': {'$and': [{'name': 'test test'}, {'properties.mass': {'$gt': 1}}]},
                'name~eq~3-hydroxymyristic acid [2-[[[5-(2,4-diketopyrimidin-1-yl)-3,4-dihydroxy-tetrahydrofuran-2-yl]methoxy-hydroxy-phosphoryl]oxy-hydroxy-phosphoryl]oxy-5-hydroxy-3-(3-hydroxytetradecanoylamino)-6-methylol-tetrahydropyran-4-yl] ester': {'name': '3-hydroxymyristic acid [2-[[[5-(2,4-diketopyrimidin-1-yl)-3,4-dihydroxy-tetrahydrofuran-2-yl]methoxy-hydroxy-phosphoryl]oxy-hydroxy-phosphoryl]oxy-5-hydroxy-3-(3-hydroxytetradecanoylamino)-6-methylol-tetrahydropyran-4-yl] ester'},
                'atomCount~lte~3.14159': {'properties.atomCount': {'$lte':  3.14159}},
                'atomCount~gte~3.14159': {'properties.atomCount': {'$gte':  3.14159}},
                'inchi~eq~InChI=1S/Na.H\n': {'inchi': 'InChI=1S/Na.H'}
                  }


        for test_query, expected in queries.items():
            mongo_query = query.to_mongo_query(test_query)
            print(test_query)
            self.assertEqual(mongo_query , expected)

    def test_invalid(self):
        queries = ['mass~eq~asdfa',
                   'mass~eq~2342gh,mass~eq~~eq~3',
                   'mass~eq~2342gh']

        for test_query in queries:
            self.assertRaises(query.InvalidQuery, query.to_mongo_query, test_query)


if __name__ == '__main__':
    unittest.main()
