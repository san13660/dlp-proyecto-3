from graphviz import Digraph
from tree import Node, separate_children
from automaton import State, Transition, AF
from direct import find_tree_values, create_direct_afd, unite_trees
from simulation import simulate_afd, simulate_afn
from atg_reader import parse_coco

import time
import traceback
import sys

if(len(sys.argv) != 2):
    print('ARGUMENTOS INVALIDOS')
    exit()

filename = sys.argv[1]
flag = True
ignore_set = set()

try:
    with open(filename, encoding='utf-8') as fp:
        content = fp.read()
    tokens, ignore_set, functions = parse_coco(content)

    parser_code = '''
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

'''
    for f in functions:
        parser_code += f.code
        parser_code += '\n'
    parser_code += '''
if(len(sys.argv) != 2):
    print('ARGUMENTOS INVALIDOS')
    exit()

filename = sys.argv[1]
tokens = scan(filename)

completed = False
while(not completed):
    try:
        '''
    parser_code += functions[0].id + '()'
    parser_code += '''
        completed = True
    except Exception as e:
        print(e)
        token_indx += 1
        if(token_indx >= len(tokens)):
            completed = True
'''
    with open('parser.py', 'w', encoding='utf-8') as fp:
        fp.write(parser_code)

    print('\n----------------parser.py CREADO----------------')
    flag = False
except:
    print(traceback.format_exc())
    print('-ERROR AL ABRIR EL ARCHIVO-\n')
    exit()

try:
    #check_for_errors(rules)
    #rules = fix_errors(rules)

    print('\n---Creando arbol---\n')

    trees = []
    symbol_ids_l = []
    alphabet = set()

    for token in tokens:
        tree = Node.initialize_tree(token.regex, token)
        alphabet.update(separate_children(tree))
        trees.append(tree)
    
    
    full_tree = unite_trees(trees)
    full_tree, symbol_ids = find_tree_values(full_tree, token)

    #print('SYMBOLS: {}'.format(symbol_ids))
    #print('ALPHABET: {}'.format(alphabet))

    #full_tree.graph_tree('Arbol_Directo', 'Arbol (Directo) - {}'.format(filename))

    print('\n---Creando AFD por metodo directo---\n')

    afd_direct = create_direct_afd(full_tree,symbol_ids,alphabet,tokens)
    afd_direct.assign_state_numbers()
    #afd_direct.graph_fsm('AFD_Directo', 'AFD (Directo) - {}'.format('ss'))

    flag=False
except Exception as e:
    print(traceback.format_exc())
    print('\n** ERROR: {} **'.format(e))


new_file = '''
from automaton import State, Transition, AF
from simulation import simulate_afd
from atg_reader import Token
import sys

def scan(filename, show_prints=False):
    afd = AF()
'''

for state in afd_direct.states:
    new_file += '    tokens = []\n'
    for token in state.tokens:
        new_file += '    tokens.append(Token(id="{}", priority={}, regex=[], is_keyword={}, except_keywords={}))\n'.format(token.id, token.priority, token.is_keyword, token.except_keywords)
    new_file += '    state = State({}, tokens)\n'.format(state.id)
    new_file += '    afd.states.append(state)\n'
    if(state == afd_direct.initial_state):
        new_file += '    afd.initial_state = state\n'
    if(state in afd_direct.final_states):
        new_file += '    afd.final_states.append(state)\n'

new_file += '    transitions = []\n'
for transition in afd_direct.transitions:
    new_file += '    transition = Transition(current_state=State({}), next_state=State({}), symbol={})\n'.format(transition.current_state.id, transition.next_state.id, transition.symbol)
    new_file += '    transitions.append(transition)\n'

new_file += '    afd.transitions = transitions\n'
new_file += '    afd.assign_state_numbers()\n'
new_file += '    ignore_set = set({})\n'.format(ignore_set)
new_file += '''
    with open(filename, encoding='utf-8') as fp:
        string = fp.read()

    char_array = []

    for s in string:
        if(ord(s) not in ignore_set):
            char_array.append(ord(s))


    tokens = simulate_afd(afd, char_array, show_prints)
    return tokens

if __name__ == "__main__":
    if(len(sys.argv) == 2):
        filename = sys.argv[1]
        scan(filename, True)
    else:
        print('ARGUMENTOS INVALIDOS')
'''

with open('scanner.py', 'w', encoding='utf-8') as fp:
    fp.write(new_file)

print('\n----------------scanner.py CREADO----------------')