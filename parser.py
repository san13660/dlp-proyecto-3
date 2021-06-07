
import sys
from scanner import scan

token_indx = 0
tokens = []

def is_next_token(token_id):
    global tokens
    global token_indx

    if(token_indx >= len(tokens)):
        raise Exception("SINTAX ERROR: pos: {}".format(token_indx))

    if(tokens[token_indx].id == token_id):
        return True
    else:
        return False

def get_last_token_value():
    global tokens
    global token_indx
    if(token_indx-1 < 0):
        raise Exception("SINTAX ERROR: {}".format(token_indx))
        return None
    
    return tokens[token_indx-1].value

def consume(token_id):
    global tokens
    global token_indx
    if(token_indx < len(tokens) and tokens[token_indx].id == token_id):
        token_indx += 1
    else:
        raise Exception("SINTAX ERROR: pos: {} | exp: '{}' | rec: '{}'".format(token_indx, token_id, tokens[token_indx].id))

def Expr():
    while(is_next_token('white')):
        consume('white')
    while(is_next_token('number') or is_next_token('(') or is_next_token('-') or is_next_token('decnumber')):
        Stat()
        consume(';')
        while(is_next_token('white')):
            consume('white')
    while(is_next_token('white')):
        consume('white')
    consume('.')

def Stat():
    value = [0]
    Expression(value)
    print("Resultado: " + str(value[0]))

def Expression(result):
    result1, result2 = [0], [0]
    Term(result1)
    while(is_next_token('+') or is_next_token('-')):
        if(is_next_token('+')):
            consume('+')
            Term(result2)
            result1[0] += result2[0]
        elif(is_next_token('-')):
            consume('-')
            Term(result2)
            result1[0] -= result2[0]
    result[0] = result1[0]

def Term(result):
    result1,result2 = [0], [0]
    Factor(result1)
    while(is_next_token('/') or is_next_token('*')):
        if(is_next_token('*')):
            consume('*')
            Factor(result2)
            result1[0] *= result2[0]
        elif(is_next_token('/')):
            consume('/')
            Factor(result2)
            result1[0] /= result2[0]
    result[0] = result1[0]

def Factor(result):
    sign = 1
    if(is_next_token('-')):
        consume('-')
        sign = -1
    if(is_next_token('number') or is_next_token('decnumber')):
        Number(result)
    elif(is_next_token('(')):
        consume('(')
        Expression(result)
        consume(')')
    result[0] *= sign

def Number(result):
    if(is_next_token('number')):
        consume('number')
    elif(is_next_token('decnumber')):
        consume('decnumber')
    result[0] = float(get_last_token_value())


if(len(sys.argv) != 2):
    print('ARGUMENTOS INVALIDOS')
    exit()

filename = sys.argv[1]
tokens = scan(filename)

completed = False
while(not completed):
    try:
        Expr()
        completed = True
    except Exception as e:
        print(e)
        token_indx += 1
        if(token_indx >= len(tokens)):
            completed = True
