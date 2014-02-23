import ntheory
import primes
import ph
import factoring
import crt
from math import log, ceil, floor, sqrt

def genPrimes(n):
    return primes.primes[5:n+5]

def genPis(l, P):
    S = []
    for i in range(0, len(P)):
        c_i = ceil(l / log(P[i], 2))
        S.append(P[i] ** c_i)
    return S

def securityConstants(n):
    #Params we need: kprime, f1, f2
    # kprime > b * log(n)
    # k = Omega(log^(3-o(1)) n) to prevent number field sieve
    b = 2 # security! TODO
    def f1(x, y): return x * y #security! TODO
    def f2(x, y): return x * y #security! TODO
    return (b * ceil(log(n, 2)), f1, f2)

def setup(n, l):
    (kprime, f1, f2) = securityConstants(n)
    k = f2(kprime, log(n, 2))    # Security param
    #l = floor(f1(k, log(n, 2))) # Block length. Weird to define it like this.
    t = ceil(n / l)        #Size of S and P
    P = genPrimes(int(t))  #Set of small primes
    S = genPis(l, P)       #Set of prime powers, all > 2^l
    for i in range(0, len(S)): S[i] = int(S[i])
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
    d = 1# primes.primes[150]
    
    #Finally, we should return |G| = m = pi_i * q * d
    m = pi_i * q * d

    return int(m)

def generateQuery(i, S):
    m = generateM(S[0], S[i])
    # We should sample from all possible G's (we don't yet)
    # Gexp then represents (g \in G)^exp
    # For now we'll return the group (gZ mod m)
    # (Note for g != 1, the order of the group here is not m)
    def Gexp(g, exp): return (g * exp) % m
    Gident = 0 #Identity element for addition is 0    
    
    # For now we'll use the group (Z mod m) (g = 1)
    g = 1 #random element of G s.t. GCD( |G:<g>|, product of all p_j's ) = 1

    q = int(m / S[i])  # q = |G| / pi_i [[ Should be an integer ]]
    h = Gexp(g, q)     # Will use this to process the response
    return {'g': g, 'Gexp': Gexp, 'Gident': 0, 'h': h, 'q': q, 'm': m}

def generateResponse(m, Gexp, g, B, S):
    (e, _) = crt.ChineseRemainder(zip(B, S))
    g_e = Gexp(g, int(e)) #g_e = g^e mod m
    return {'e':e, 'g_e':g_e}

def processResponse(Gexp, pi_i, g_e, q, h, m):
    h_e = Gexp(g_e, q)
    # "C_i is the discrete logarithm of h_e with respect to base h"
    # => h^C_i = h_e. ie) Gexp(h, C_i) = h_e

    #TODO: Should use pohlig-hellman wrapper around bs-gs 
    #  since the modulus m is composite (will be faster) 
    C_i = babyStepGiantStep(Gexp, h, h_e, m)
    return C_i

# Solve for alpha^x = beta in a cyclic group of order n
def babyStepGiantStep(Gexp, alpha, beta, n):
    m = int(ceil(sqrt(n)))
    table = {}
    for j in range(0, m):
        table[Gexp(alpha, j)] = j
    ai = Gexp(alpha, -1 * m)
    gamma = beta
    ret = 0
    for i in range(0, m - 1):
        if(gamma in table): return i*m + table[gamma]
        gamma = gamma * Gexp(alpha, -1 * m)
    return ret
