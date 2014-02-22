import ntheory
import primes
import ph
import factoring
import crt
from math import log, ceil, floor
#Gi is the set of cyclic groups whose order is a number in [2^k, 2^(k+1)] and is divisible by pi_i

def SampleG(i):
    return 1

def kprime(_):
    return 1

def f1(x, y):
    return 1

def f2(x, y):
    return 1

def D(_): 
    return 1


def genPrimes(n):
    return primes.primes[5:n+5]

def genPis(l, P):
    S = []
    for i in range(0, len(P)):
        c_i = ceil(l / log(P[i], 2))
        S.append(P[i] ** c_i)
    return S

def securityConstants():
    #Params we need: kprime, f1, f2
    # kprime > b * log(n)
    # k = Omega(log^(3-o(1)) n) to prevent number field sieve
    b = 2 # security! TODO
    def f1(x, y): return x * y #security! TODO
    def f2(x, y): return x * y #security! TODO
    return (b * ceil(log(n, 2)), f1, f2)

def setup(n, l):
    (kprime, f1, f2) = securityConstants()
    k = f2(kprime, log(n, 2)) #Security param
    #l = floor(f1(k, log(n, 2))) #Security integer

    # given default sec constants, l is (6 log(n))
    t = ceil(n / l)  #Size of S and P
    P = genPrimes(int(t))    #Set of small primes
    S = genPis(l, P)    #Set of prime powers, all > 2^l
    return {'k':k, 'l':l, 't':t, 'P':P, 'S':S}

# Generate a modulus m that phi-hides pi_i [pi_i divides phi(m)]
#   (this is how we define the cyclic group G)
def generateMSecure(pi_i):
    # Choose random "semi-safe" prime Q_0 = 2(q_0)(pi_i) + 1
    #   and random "semi-safe" prime Q_1 = 2d(q_1) + 1
    #   then m = (Q_0)(Q_1)
    # Security requirements:
    #   pi_i < m^(1/4)
    # For testing we'll start with q0 = primes[10000] and Q1 = primes[10700]
    #   this is NOT GOOD for security 
    #   d & q1 need to be chosen uniformally from a large interval 
    # Note also that m must be within [2k , 2(k+1)] for security (since it's the order of G)
    d = primes.primes[150]
    Q0 = 4
    i = 100
    while not primes.is_prime(int(Q0)):
        q_0 = primes.primes[i]
        i = i + 1
        Q0 = 2 * (q_0) * (pi_i) + 1
    Q1 = 4
    i = 107
    while not primes.is_prime(Q1):
        q_1 = primes.primes[i]
        i = i + 1
        Q1 = 2 * d * (q_1)  + 1
    m = Q0 * Q1
    return m

#Unlike the previous method, this one produces an integer value
#  that is divisible by pi_i
def generateM(pi_0, pi_i):
    #q should be sampled from
    # [2^k', 2^k' + 1] and be a factor/divisor? of pi_0 * pi_1
    f = factoring.factor( pi_0 * pi_i )
    q = f[0]

    #d should be sampled from
    # [2^k / (q * pi_i), 2^(k+1) / (q * pi_i) ]
    # where all prime divisors of d are less than q
    d = primes.primes[150]
    
    #Finally, we should return |G| = m = pi_i * q * d
    m = pi_i * q * d

    return int(m)

def generateQuery(i, S):
    g = primes.primes[40] #random element of G s.t. GCD( |G:<g>|, product of all p_j's ) = 1
    m = generateM(S[0], S[i])
    q = int(m / S[i])  # q = |G| / pi_i [[ Should be an integer ]]
    h = pow(g, q, m)   # Will use this to process the response
    return {'g': g, 'h': h, 'q': q, 'm': m}

def generateResponse(m, g, B, S):
    (e, _) = crt.ChineseRemainder(zip(B, S))
    g_e = pow(g, int(e), m) #g_e = g^e mod m
    return g_e

def processResponse(g_e, q, h, m):
    h_e = pow(g_e, q, m)
    C_i = ph.PohligHellmanModP(h, h_e, m)
    #Above: C_i is the discrete logarithm log_h(h_e) within the subgroup
    # H \subset G of order pi_i = p_i^(c_i) 
    return C_i

#Establish test block values
C = [100, 101, 102, 103, 104, 105]

#Get an upper bound on block size
max = 0
for i in range(0, len(C)):
    l = ceil(log(C[i], 2))
    if l > max: max = l
l = 2 * max

#Get database size
n = len(C) * l

print "Database: " + str(C)
print "l (chunk length): " + str(l)
print "n (database size): " + str(n)

params = setup(n, l)
print "Parameters: " + str(params)

#Prime power size security test
pow2l = str(2 ** l)
for i in range(0, len(params['P'])): 
    if(params['P'][i] >= pow2l): print "Prime Power too small"

#Generate a query
i = 2
query = generateQuery(i, params['S'])
print "Query: " + str(query)

#Generate a response
response = generateResponse(query['m'], query['g'], C, params['S'])
print "Response: " + str(response)

#Process Response
proc_response = processResponse(response, query['q'], query['h'], query['m'])
