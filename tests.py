from blowship import *
import unittest
import random

class TestPIR(unittest.TestCase):
    def setUp(self):
        #Establish test block values
        self.C = []
        for i in range(0, 20): self.C.append(2 ^ 1024 * i + i)

        #Get an upper bound on block size
        max = 0
        for i in range(0, len(self.C)):
            l = ceil(log(self.C[i], 2))
            if l > max: max = l
        self.l = 2 * max                   # Max block size
        self.n = int(len(self.C) * self.l) # Database size
        self.params = setup(self.n, self.l)

    # Prime power size security test    
    #   All prime powers pi_i should be > 2^l
    def test_pi_sizes(self):
        pow2l = 2 ** self.l
        for i in range(0, len(self.params['S'])): 
            self.assertTrue(self.params['S'][i] >= pow2l)

    # Test that when we make a query for block i, |G| is divisible by pi_i.
    #   Once we get large enough numbers this test might be infeasible
    #   Since ideally the server shouldn't be able to perform this test.
    def test_order_divisible_pii(self):
        for i in range(0, len(self.C)):
            query = generateQuery(i, self.params['S'])                
            self.assertTrue( query['m'] % self.params['S'][i] == 0)
        
    # Test that forall i, e mod (pi_i) = C_i.
    #   Using the prime associated with the block index we want,
    #   we get that block back when modding the db number with that prime
    #   (This is given if we use CRT correctly)
    def test_database_number(self):
        #Perform an initial query on any i in order to get back m
        i = 2
        query = generateQuery(i, self.params['S'])                
        response = generateResponse(query['m'], query['Gexp'], query['g'], self.C, self.params['S'])
        for i in range(0, len(self.C)):
            self.assertTrue(response['e'] % self.params['S'][i] == self.C[i])

    #This follows from the CORRECTNESS OF RESPONSE RETRIEVAL section
    def test_correctness_retrieval(self):
        i = 1
        query = generateQuery(i, self.params['S'])                
        response = generateResponse(query['m'], query['Gexp'], query['g'], self.C, self.params['S'])

        Gexp = query['Gexp']
        C_i = self.C[i]
        pi_i = self.params['S'][i]
        m = query['m']
        q = query['q']
        g = query['g']
        g_e = response['g_e']
        e = response['e']
        
        # h_e = g_e ^ (m / pi_i)                -- by definition
        h_e = Gexp(g_e, q)
        self.assertTrue(h_e == Gexp(g_e, m / pi_i))

        # g_e ^ (m / pi_i) = g ^ (e * m / pi_i) -- by definition
        self.assertTrue(Gexp(g_e, m / pi_i) == Gexp(g, e * m / pi_i))

        # g ^ (e * m / pi_i) =  g ^ (C_i * m / pi_i) -- by magic
        self.assertTrue(Gexp(g, e * m / pi_i) == Gexp(g, C_i * m / pi_i) )
        
        # g ^ (C_i * m / pi_i) = h ^ C_i             -- by magic
        h = Gexp(g, q)
        self.assertTrue(Gexp(g, C_i * m / pi_i) == Gexp(h, C_i))
        
        #This line of equational reasoning means that h_e = h ^ C_i
        self.assertTrue(h_e == Gexp(h, C_i))

        #" Notice that G contains a subgroup H of order pi_i, 
        #   and that h = g^q is a generator of H"
        # => h ^ pi_i = Identity Element (Since order of (H=<h>) is pi_i)
        # (Identity element is 0 for addition, 1 for multiplication)
        self.assertTrue( Gexp(h, pi_i) == query['Gident'])


    # One whole cycle of query, response, process
    def test_process_response(self):
        for i in range(0, len(self.C)):
            pi_i = self.params['S'][i]
            query = generateQuery(i, self.params['S'])                
            response = generateResponse(query['m'], query['Gexp'], query['g'], self.C, self.params['S'])
            proc_response = processResponse(query['Gexp'], pi_i, response['g_e'], query['q'], query['h'], query['m'])
            self.assertTrue( proc_response == self.C[i])

if __name__ == '__main__':
    unittest.main()
