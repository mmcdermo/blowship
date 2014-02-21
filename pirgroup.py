import ntheory
import primes
import pohlig_hellman
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
        c_i = (l / log(P[i], 2)).ceil()
        pi[i] = P[i] ** c_i
    return S

def setup(n):
    k = f2(kprime, log(n, 2)) #Security param
    l = (f1(k, log(n, 2))).floor() #Security integer
    t = (n / l).ceil()  #Size of S and P
    P = genPrimes(t)    #Set of small primes
    S = genPis(l, P)    #Set of prime powers, all > 2^l
    return (k, l, t, P, S)

# Generate a modulus m that phi-hides pi_i [pi_i divides phi(m)]
#   (this is how we define the cyclic group G)
def generateG(pi_i):
    # Choose random "semi-safe" prime Q_0 = 2(q_0)(pi_i) + 1
    #   and random "semi-safe" prime Q_1 = 2d(q_1) + 1
    #   then m = (Q_0)(Q_1)
    # Security requirements:
    #   pi_i < m^(1/4)
    # For testing we'll start with q0 = primes[10000] and Q1 = primes[10700]
    #   this is NOT GOOD for security 
    #   d & q1 need to be chosen uniformally from a large interval 
    d = primes.primes[150]
    Q0 = 4
    i = 100
    while not primes.is_prime(Q0):
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



def groupExp(g, exp):
    return g # Obviously wrong

def generateQuery(i, f1, f2, S, D, ki1):
    G = SampleG(i)
    g = 1 #random element of G s.t. GCD( |G:<g>|, product of all p_j's ) = 1
    lenGroup = 1 #length of cyclic group <g>
    q = lenGroup / S[i] #keep this private
    return ( (G,g), q )

def generateResponse(B, f1, f2, S, G, g, ki1):
    e = chinese_remainder_theory(zip(B, S))
    m = _
    g_e = pow(g, e, m) #g_e = g^e mod m
    return g_e

def processResponse(pi_i, g_e, G, q, h, ki1):
    h_e = pow(g_e, q, m)
    C_i = phlog(h, h_e, pi_i, p_i, c_i)

    #def phlog(p,n,alpha,beta,q,c):

      #Above: C_i is the discrete logarithm log_h(h_e) within the subgroup
      # H \subset G of order pi_i = p_i^(c_i) 
    return C_i
