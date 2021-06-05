FIND_COMPILER_HEADER = 0
READ_COMPILER_NAME = 1
FIND_CHARACTERS_HEADER = 2
CHARACTER_NAME = 3
CHARACTER_DEFINITION = 4
KEYWORD_NAME = 5
KEYWORD_DEFINITION = 6
TOKEN_NAME = 7
TOKEN_DEFINITION = 8
IGNORE = 9
PRODUCTION_NAME = 10
PRODUCTION_DEFINITION = 11
END = 12

current_token_priority = 0

INDENT = '    '

class Token():
    def __init__(self, id, priority, regex, is_keyword=False, except_keywords=False):
        self.id = id
        self.priority = priority
        self.is_keyword = is_keyword
        self.except_keywords = except_keywords
        self.regex = regex
        self.value = ''

    def __repr__(self):
        string_regex = ''
        for r in self.regex:
            if(type(r) is int):
                string_regex += chr(r)
            else:
                string_regex += r
        return '(ID: {} | VALUE: {})'.format(self.id, self.value)

class CharacterSet:
    def __init__(self, id):
        self.id = id
        self.include = set()
    
    def __contains__(self, key):
        return key in self.include

    def __str__(self):
        return 'ID:{} | SET:{}'.format(self.id, repr(self.include))

    def add(self, s):
        if(type(s) is int):
            self.include.add(s)
        else:
            s = set(s)
            self.include.update(s)

    def discard(self, s):
        if(type(s) is int):
            self.include.discard(s)
        else:
            s = set(s)
            self.include = self.include-s

    def add_any(self):
        for i in range(256):
            self.include.add(i)

    def add_range(self, start, end):
        for i in range(start, end+1):
            self.include.add(i)

class Function:
    def __init__(self, id):
        self.id = id
        self.code = ''
        self.first_pos = set()
        self.raw = ''

def create_keyword(id, string, token_priority):
    print('KEYWORD\n{}: {}'.format(id, string))
    string = string.strip()
    buffer = []
    for s in string:
        if(s == '"' or s == ' '):
            continue
        buffer.append(ord(s))
    
    token = Token(id, token_priority, buffer, is_keyword=True)
    print(token)
    print('')
    return token
    


def create_character_set(id, string, character_sets):
    print('CHARACTER\n{}: {}'.format(id, string))
    string = string.strip()
    inside_quotes = False
    char_range = False
    last_char = -1
    operation = '+'
    character_set = CharacterSet(id)
    buffer = ''
    for s in string:
        if(s == '"' or s== "'"):
            buffer = ''
            inside_quotes = not inside_quotes
            continue

        if(inside_quotes):
            if(char_range):
                    character_set.add_range(last_char,ord(s))
                    last_char = -1
                    char_range = False
            elif(operation == '+'):
                character_set.add(ord(s))
                last_char = int(ord(s))
            elif(operation == '-'):
                character_set.discard(ord(s))
            else:
                raise Exception("Caracter invalido")
            buffer = ''
        else:
            if(s == ' '):
                continue
            if(s == '+'):
                operation = '+'
                continue
            elif(s == '-'):
                operation = '-'
                continue

            if(buffer.startswith('CHR(') and s == ')'):
                if(char_range):
                    character_set.add_range(last_char,int(buffer[4:]))
                    last_char = -1
                    char_range = False
                elif(operation == '+'):
                    character_set.add(int(buffer[4:]))
                    last_char = int(buffer[4:])
                elif(operation == '-'):
                    character_set.discard(int(buffer[4:]))
                else:
                    raise Exception("Caracter invalido")
                operation = ''
                buffer = ''
                continue
            
            buffer += s

            if(buffer=='ANY'):
                character_set.add_any()
                buffer = ''
            elif(buffer=='..'):
                char_range = True
                buffer = ''
            else:
                for c in character_sets:
                    if(buffer==c.id):
                        if(operation == '+'):
                            character_set.add(c.include)
                        elif(operation == '-'):
                            print('DISCARD: {} {}'.format(buffer, c.include))
                            character_set.discard(c.include)
                        else:
                            raise Exception("Caracter invalido")
                        buffer = ''

    print(character_set)
    print('')
    return character_set


def create_token_definition(id, string, character_sets, token_priority):
    print('TOKEN\n{}: {}'.format(id, string))
    string = string.strip()
    buffer = ''

    inside_quotes = False
    except_keywords = False

    regex = []

    for indx in range(len(string)):
        s = string[indx]
        if(s == '"'):
            buffer = ''
            inside_quotes = not inside_quotes
            continue

        if(inside_quotes):
            #if(s in '()|*?+\\'):
                #regex += ord('\\')
            regex.append(ord(s))
            continue
        
        if(s == '{'):
            regex.append('(')
            continue
        elif(s == '}'):
            regex.append(')')
            regex.append('*')
            continue
        elif(s == '['):
            regex.append('(')
            continue
        elif(s == ']'):
            regex.append(')')
            regex.append('?')
            continue
        elif(s == '|'):
            regex.append('|')
            continue
        
        buffer += s

        if(buffer.strip() == 'EXCEPT KEYWORDS'):
            except_keywords = True
            buffer = ''
            continue
        
        if(indx+1 == len(string) or string[indx+1] in ' |}{[]"'):
            for c in character_sets:
                if(buffer.strip()==c.id):
                    regex.append('(')
                    for o in c.include:
                        #if(o in '()|*?+\\'):
                        #    new_string += '\\'
                        regex.append(o)
                        regex.append('|')
                    regex.pop()
                    regex.append(')')
                    buffer = ''
    
    token = Token(id, token_priority, regex, except_keywords=except_keywords)
    print(token)
    print('')
    return token

def gen_line(content, level):
    line = ''
    for i in range(level):
        line += INDENT

    line += content
    return line

def gen_function(function_name, content, tokens, functions):
    function_name = function_name.strip()
    if('<' in function_name and '>' in function_name):
        function_name = function_name.replace('<','(')
        function_name = function_name.replace('>',')')
        function_name = function_name.replace('ref ','')
        function_name = function_name.replace('double ','')
    else:
        function_name += '()'

    output = 'def ' + function_name + ':\n'

    found_tokens, lines = recursive_build_function(content, tokens, 1, functions)

    for line in lines:
        output += line
        output += '\n'

    return output, found_tokens

def recursive_build_function(content, tokens, level, functions, insert_ifs = False):
    global current_token_priority

    found_tokens = set()
    output = []

    content = content.strip()
    if(not content):
        return found_tokens, output

    
    if(insert_ifs and '|' not in content):
        insert_ifs = False

    if_index = -1
    if(insert_ifs):
        level += 1
        if_index = len(output)
        output.append(gen_line('if(',level-1))

    if_conditions = 0
    inside_quotes = False
    inside_code = False
    code_buffer = ''
    new_token = ''
    buffer = ''

    i = -1
    while(i+1 < len(content)):
        i += 1
        c = content[i]
        if(inside_code):
            if(c == '.' and content[i+1] == ')'):
                continue

            if(c == ')' and content[i-1] == '.'):
                inside_code = False
                new_line = gen_line(code_buffer, level)
                output.append(new_line)
                code_buffer = ''
            else:
                code_buffer += c
            continue

        if(c == '(' and content[i+1] == '.'):
            continue
        if(c == '.' and content[i-1] == '('):
            inside_code = True
            continue

        if(c == '"'):
            if(inside_quotes):
                #print('New Token: {}'.format(new_token))
                current_token_priority += 1
                regex = []
                for s in new_token:
                    regex.append(ord(s))
                tokens.append(Token(new_token,current_token_priority, regex))
                new_line = gen_line("consume('{}')".format(new_token), level)
                output.append(new_line)
                if(if_conditions==0):
                    found_tokens.add(new_token)
                    if(insert_ifs):
                        output[if_index] += "is_next_token('{}') or ".format(new_token)
                    if_conditions += 1
                new_token = ''
            inside_quotes = not inside_quotes
            continue

        if(inside_quotes):
            new_token += c
            continue

        if(c in '({['):
            end = find_parenthesis_end(content, i)
            new_level = level
            if(c in'{['):
                new_level += 1
            conditions, new_lines = recursive_build_function(content[i+1:end], tokens, new_level, functions, True)
            if(if_conditions == 0):
                found_tokens.update(conditions)
                if(c == '('):
                    if_conditions += 1
            if(c == '{'):
                line = 'while('
                for condition in conditions:
                    line += "is_next_token('{}')".format(condition)
                    line += ' or '
                line = line[:-4]
                line += '):'
                line = gen_line(line, level)
                output.append(line)
            elif(c == '['):
                line = 'if('
                for condition in conditions:
                    line += "is_next_token('{}')".format(condition)
                    line += ' or '
                line = line[:-4]
                line += '):'
                line = gen_line(line, level)
                output.append(line)
            output += new_lines
            i = end
            continue

        if(c == '|'):
            if(not insert_ifs):
                raise Exception("Error OR")
            if(if_conditions == 0):
                output[if_index] += "next_token == 'ANY'):"
            else:
                output[if_index] = output[if_index][:-4]
                output[if_index] += '):'

            if_index = len(output)
            output.append(gen_line('elif(',level-1))
            if_conditions = 0

            continue

        buffer += c

        if(i+1 == len(content) or content[i+1] in '   \n()}{[]|"'):
            buffer = buffer.strip()
            if(not buffer):
                continue
            found = False
            for t in tokens:
                if(t.id == buffer):
                    found = True
                    break
            if(found):
                new_line = gen_line("consume('{}')".format(buffer), level)
                if(if_conditions==0):
                    found_tokens.add(t.id)
                    if(insert_ifs):
                        output[if_index] += "is_next_token('{}') or ".format(buffer)
                    if_conditions += 1
            else:
                buffer = buffer.strip()
                f1_name = buffer[:].strip()
                if('<' in buffer and '>' in buffer):
                    f1_name = buffer[:buffer.index('<')]
                    buffer = buffer.replace('<','(')
                    buffer = buffer.replace('>',')')
                    buffer = buffer.replace('ref ','')
                    buffer = buffer.replace('double ','')
                else:
                    buffer += '()'
                new_line = gen_line(buffer, level)
                if(if_conditions == 0):
                    for f in functions:
                        f2_name = f.id
                        if('<' in f2_name):
                            f2_name = f2_name[:f2_name.index('<')]
  
                        if(f1_name == f2_name):
                            found_tokens.update(f.first_pos)
                            

                            if(insert_ifs):
                                for fp in f.first_pos:
                                    output[if_index] += "is_next_token('{}') or ".format(fp)
                            break
                    if_conditions += 1
            output.append(new_line)

            #print('Buffer: {}'.format(buffer))
            buffer = ''
    if(insert_ifs):
        if(if_index == 0):
            output.pop(0)
        else:
            if(if_conditions > 0):
                output[if_index] = output[if_index][:-4]
                output[if_index] += '):'
            else:
                output[if_index] = gen_line('else:', level-1)

    return found_tokens, output

def find_parenthesis_end(content, start):
    end = -1
    symbol = ''
    openings = 0
    for i in range(start, len(content)):
        c = content[i]
        if(symbol):
            if(c == symbol):
                openings += 1
            elif(symbol == '(' and c == ')'):
                openings -= 1
            elif(symbol == '{' and c == '}'):
                openings -= 1
            elif(symbol == '[' and c == ']'):
                openings -= 1
            if(openings == 0):
                end = i
                break
        else:
            if(c in '({['):
                symbol = c
                openings += 1
                start = i

    return end

def parse_function(function_name, content, tokens):
    function_name = function_name.strip()
    if('<' in function_name and '>' in function_name):
        function_name = function_name.replace('<','(')
        function_name = function_name.replace('>',')')
        function_name = function_name.replace('ref ','')
        function_name = function_name.replace('double ','')
    else:
        function_name += '()'

    output = 'def ' + function_name + ':\n'

    inside_parenthesis = False
    inside_quotes = False
    inside_code = False
    inside_while = 0

    new_token = ''

    buffer = ''
    code_buffer = ''

    conditions = []
    body = ''

    for i in range(len(content)):
        c = content[i]

        if(inside_code):
            if(c == '.' and content[i+1] == ')'):
                continue

            if(c == ')' and content[i-1] == '.'):
                inside_code = False
            else:
                code_buffer += c
            continue

        if(c == '(' and content[i+1] == '.'):
            continue
        if(c == '.' and content[i-1] == '('):
            inside_code = True
            output += '    '
            continue


        if(c == '"'):
            if(inside_quotes):
                print('New Token: {}'.format(new_token))
                new_token = ''
            inside_quotes = not inside_quotes
            continue
        
        if(c == '{'):
            #output += 'while('
            inside_while += 1
            conditions = 'while('
            print('ENTRANDO WHILE')
            continue
        if(c == '}'):
            inside_while -= 1
            conditions = conditions[:-5]
            conditions += '):'
            print('WHILE: ' + conditions)
            print('SALIENDO WHILE')
            continue

        if(inside_quotes):
            new_token += c
            continue

        if(c == '('):
            inside_parenthesis = True
            print('ENTRANDO PARENTESIS')
            continue

        if(c == ')'):
            inside_parenthesis = False
            print('SALIENDO PARENTESIS')
            continue

        buffer += c

        if(i+1 == len(content) or content[i+1] in '   \n()}{|"'):
            buffer = buffer.strip()
            if(not buffer):
                continue
            found = False
            for t in tokens:
                if(t.id == buffer):
                    found = True

            if(inside_while > 1):
                if(found):
                    conditions += buffer
                    conditions += ' or '

            print('Buffer: {}'.format(buffer))
            buffer = ''
            
    print(output)


def parse_coco(content):
    global current_token_priority
    ignored_chars = ' '
    string_buffer = ''

    name = ''

    current_state = FIND_COMPILER_HEADER

    character_sets = []
    tokens = []
    functions = []

    current_character = ''
    open_quotes = False
    inside_code= False

    out_file = ''

    ignore_set = set() 

    for i in range(len(content)):
        char = content[i]
        if(current_character == END):
            break

        if(current_state == FIND_COMPILER_HEADER):
            string_buffer += char
            if(char == '\n'):
                string_buffer = ''
            if(string_buffer == 'COMPILER '):
                current_state = READ_COMPILER_NAME
                string_buffer = ''
        elif(current_state == READ_COMPILER_NAME):
            if(char in ignored_chars):
                continue
            string_buffer += char
            if(char == '\n'):
                name = string_buffer
                print('COMPILER: {}'.format(name))
                string_buffer = ''
                current_state = FIND_CHARACTERS_HEADER
        elif(current_state == FIND_CHARACTERS_HEADER):
            if(char in ignored_chars):
                continue
            if(char == '\n'):
                string_buffer = ''
                continue
            string_buffer += char
            if(string_buffer == 'CHARACTERS'):
                string_buffer = ''
                current_state = CHARACTER_NAME
                print('READING CHARACTERS')
        elif(current_state == CHARACTER_NAME):
            if(char in ignored_chars):
                continue
            if(char == '\n'):
                string_buffer = ''
                continue
            if(char == '='):
                current_character = string_buffer
                string_buffer = ''
                current_state = CHARACTER_DEFINITION
                continue
            
            string_buffer += char
            if(string_buffer == 'KEYWORDS'):
                current_state = KEYWORD_NAME
        elif(current_state == CHARACTER_DEFINITION):
            if(char == '"'):
                open_quotes = not open_quotes
            if(char == '.' and not open_quotes and (content[i+1] != '.' and content[i-1] != '.')):
                character_sets.append(create_character_set(current_character, string_buffer, character_sets))
                string_buffer = ''
                current_state = CHARACTER_NAME
            else:
                string_buffer += char
        elif(current_state == KEYWORD_NAME):
            if(char in ignored_chars):
                continue
            if(char == '\n'):
                string_buffer = ''
                continue
            if(char == '='):
                current_character = string_buffer
                string_buffer = ''
                current_state = KEYWORD_DEFINITION
                continue
            
            string_buffer += char
            if(string_buffer == 'TOKENS'):
                current_state = TOKEN_NAME

        elif(current_state == KEYWORD_DEFINITION):
            if(char == '"'):
                open_quotes = not open_quotes
            if(char == '.' and not open_quotes):
                tokens.append(create_keyword(current_character, string_buffer, current_token_priority))
                current_token_priority += 1
                string_buffer = ''
                current_state = KEYWORD_NAME
            else:
                string_buffer += char
        elif(current_state == TOKEN_NAME):
            if(char in ignored_chars):
                continue
            if(char == '\n'):
                string_buffer = ''
                continue
            if(char == '='):
                current_character = string_buffer
                string_buffer = ''
                current_state = TOKEN_DEFINITION
                continue
            
            string_buffer += char
            if(string_buffer == 'PRODUCTIONS'):
                current_state = PRODUCTION_NAME
            elif(string_buffer.strip() == 'IGNORE'):
                current_state = IGNORE
                string_buffer = ''

        elif(current_state == TOKEN_DEFINITION):
            if(char == '"'):
                open_quotes = not open_quotes
            if(char == '.' and not open_quotes):
                tokens.append(create_token_definition(current_character, string_buffer, character_sets, current_token_priority))
                current_token_priority += 1
                string_buffer = ''
                current_state = TOKEN_NAME
            else:
                string_buffer += char

        elif(current_state == IGNORE):
            if(char == ' ' or char == '\n'):
                for character_set in character_sets:
                    if(character_set.id == string_buffer.strip()):
                        ignore_set = character_set.include
                        current_state = END
                        break
            else:
                string_buffer += char

        elif(current_state == PRODUCTION_NAME):
            if(char == '\n'):
                string_buffer = ''
                continue
            if(char == '='):
                current_character = string_buffer
                string_buffer = ''
                current_state = PRODUCTION_DEFINITION
                continue
            
            string_buffer += char
            if(string_buffer == 'END'):
                current_state = END
            elif(string_buffer.strip() == 'IGNORE'):
                current_state = IGNORE
                string_buffer = ''

        elif(current_state == PRODUCTION_DEFINITION):
            if(char == '"'):
                open_quotes = not open_quotes
            if(char == '.' and content[i-1] == '('):
                inside_code = True
            if(char == ')' and content[i-1] == '.'):
                inside_code = False
            if(char == '.' and not open_quotes and not inside_code):
                #parse_function(current_character, string_buffer, tokens)

                # GUARDAR TEXTO FUNCIONES, RECORRERLAS EN SENTIDO OPUESTO functions=[]
                function_name = current_character.strip()
                new_function = Function(function_name)
                new_function.raw = string_buffer
                functions.append(new_function)
                string_buffer = ''
                current_state = PRODUCTION_NAME
            else:
                string_buffer += char

    for f in reversed(functions):
        code_lines, first_pos = gen_function(f.id, f.raw, tokens, functions)
        f.code = code_lines
        f.first_pos = first_pos
        print('{}: first_pos{}'.format(f.id, f.first_pos))

    return tokens, ignore_set, functions