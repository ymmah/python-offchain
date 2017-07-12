from __future__ import print_function
import argparse
import sys
import re

__DBG__ = False


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class WASM_OP_Code:
    type_ops = [('i32', '7f'), ('i64', '7e'), ('f32', '7d'),
                ('f64', '7c'), ('anyfunc', '7b'), ('func', '60'),
                ('empty_block_type', '40')]
    type_ops_dict = dict(type_ops)

    control_flow_ops = [{'unreachable', '00'}, {'nop', '01'},
                        {'block', '02'}, {'loop', '03'},
                        {'if', '04'}, {'else', '05'},
                        {'end', '0b'}, {'br', '0c'},
                        {'br_if', '0d'}, {'br_table', '0e'},
                        {'return', '0f'}]
    control_flow_ops_dict = dict(control_flow_ops)

    call_ops = [{'call', '10'}, {'call_indirect', '11'}]
    call_ops_dict = dict(call_ops)

    param_ops = [{'drop', '1a'}, {'select', '1b'}]
    param_ops_dict = dict(param_ops)

    var_access = [{'get_local', '20'}, {'set_local', '21'},
                    {'tee_local', '22'}, {'get_global', '23'},
                    {'set_global', '24'}]
    var_access_dict = dict(var_access)

    mem_ops = [{'i32.load', '28'}, {'i64.load', '29'},
                {'f32.load', '2a'}, {'f64.load', '2b'},
                {'i32.load8_s', '2c'}, {'i32.load8_u', '2d'},
                {'i32.load16_s', '2e'},  {'i32.load16_u', '2f'},
                {'i64.load8_s', '30'}, {'i64.load8_u', '31'},
                {'i64.load16_s', '32'}, {'i64.load16_u', '33'},
                {'i64.load32_s', '34'}, {'i64.load32_u', '35'},
                {'i32.store', '36'}, {'i64.store', '37'},
                {'f32.store', '38'}, {'f64.store', '39'},
                {'i32.store8', '3a'}, {'i32.store16', '3b'},
                {'i64.store8', '3c'}, {'i64.store16', '3d'},
                {'i64.store32', '3e'}, {'current_memory', '3f'},
                {'grow_memory', '40'}]
    mem_ops_dict = dict(mem_ops)

    consts = [{'i32.const', '41'}, {'i64.const', '42'},
              {'f32.const', '43'}, {'f64', '44'}]
    consts_dict = dict(consts)

    comp_ops = [{'i32.eqz', '45'}, {'i32.eq', '46'}, {'i32.ne', '47'},
                {'i32.lt_s', '48'}, {'i32.lt_u', '49'},
                {'i32.gt_s', '4a'}, {'i32.gt_u', '4b'},
                {'i32.le_s', '4c'}, {'i32.le_u', '4d'},
                {'i32.ge_s', '4e'}, {'i32.ge_u', '4f'},
                {'i64.eqz', '50'}, {'i64.eq', '51'},
                {'i64.ne', '52'}, {'i64.lt_s', '53'},
                {'i64.lt_u', '54'}, {'i64.gt_s', '55'},
                {'i64.gt_u', '56'}, {'i64.le_s', '57'},
                {'i64.le_u', '58'}, {'i64.ge_s', '59'},
                {'i64.ge_u', '5a'}, {'f32.eq', '5b'},
                {'f32.ne', '5c'}, {'f32.lt', '5d'},
                {'f32.gt', '5e'}, {'f32.le', '5f'},
                {'f32.ge', '60'}, {'f64.eq', '61'},
                {'f64.ne', '62'}, {'f64.lt', '63'},
                {'f64.gt', '64'}, {'f64.le', '65'},
                {'f64.ge', '66'}]
    comp_ops_dict = dict(comp_ops)

    num_ops = [{'i32.clz', '67'}, {'i32.ctz', '68'},
               {'i32.popcnt', '69'}, {'i32.add', '6a'},
               {'i32.sub', '6b'}, {'i32.mul', '6c'},
               {'i32.div_s', '6d'}, {'i32.div_u', '6e'},
               {'i32.rem_s', '6e'}, {'i32.rem_u', '70'},
               {'i32.and', '71'}, {'i32.or', '72'},
               {'i32.xor', '73'}, {'i32.shl', '74'},
               {'i32.shr_s', '75'}, {'i32.shr_u', '76'},
               {'i32.rotl', '77'}, {'i32.rotr', '78'},
               {'i64.clz', '79'}, {'i64.ctz', '7a'},
               {'i64.popcnt', '7b'}, {'i64.add', '7c'},
               {'i64.sub', '7d'}, {'i64.mul', '7e'},
               {'i64.div_s', '7f'}, {'i64.div_u', '80'},
               {'i64.rem_s', '81'}, {'i64.rem_u', '82'},
               {'i64.and', '83'}, {'i64.or', '84'},
               {'i64.xor', '85'}, {'i64.shl', '86'},
               {'i64.shr_s', '87'}, {'i64.shr_u', '88'},
               {'i64.rotl', '89'}, {'i63.rotr', '8a'},
               {'f32.abs', '8b'}, {'f32.neg', '8c'},
               {'f32.ceil', '8d'},  {'f32.floor', '8e'},
               {'f32.trunc', '8f'}, {'f32.nearest', '90'},
               {'f32.sqrt', '91'}, {'f32.add', '92'},
               {'f32.sub', '93'}, {'f32.mul', '94'},
               {'f32.div', '95'}, {'f32.min', '96'},
               {'f32.max', '97'}, {'f32.copysign', '98'},
               {'f64.abs', '99'}, {'f64.neg', '9a'},
               {'f64.ceil', '9b'}, {'f64.floor', '9c'},
               {'f64.trunc', '9d'}, {'f64.nearest', '9e'},
               {'f64.sqrt', '9f'}, {'f64.add', 'a0'},
               {'f64.sub', 'a1'}, {'f64.mul', 'a2'},
               {'f64.div', 'a3'}, {'f64.min', 'a4'},
               {'f64.max', 'a5'}, {'f64.copysign', 'a6'}]
    num_ops_dict = dict(num_ops)

    conversion = [{'i32.wrap/i64', 'a7'},
                    {'i32.trunc_s/f32', 'a8'},
                    {'i32.trunc_u/f32', 'a9'},
                    {'i32.trunc_s/f64', 'aa'},
                    {'i32.trunc_u/f64', 'ab'},
                    {'i64.extend_s/i32', 'ac'},
                    {'i64.extend_u/i32', 'ad'},
                    {'i64.trunc_s/f32', 'ae'},
                    {'i64.trunc_u/f32', 'af'},
                    {'i64.trunc_s/f64', 'b0'},
                    {'i64.trunc_u/f64', 'b1'},
                    {'f32.convert_s/i32', 'b2'},
                    {'f32.convert_u/i32', 'b3'},
                    {'f32.convert_s/i64', 'b4'},
                    {'f32.convert_u/i64', 'b5'},
                    {'f32.demote/f64', 'b6'},
                    {'f64.convert_s/i32', 'b7'},
                    {'f64.convert_u/i32', 'b8'},
                    {'f64.convert_s/i64', 'b9'},
                    {'f64.convert_u/i64', 'ba'},
                    {'f64.promote/f32', 'bb'}]
    conversion_dict = dict(conversion)

    reinterpretations = [{'i32.reinterpret/f32', 'bc'},
                         {'i64.reinterpret/f64', 'bd'},
                         {'f32.reinterpret/i32', 'be'},
                         {'f64.reinterpret/i64', 'bf'}]
    reinterpretations_dict = dict(reinterpretations)

    section_code = [{'type', '01'}, {'import', '02'},
                    {'function', '03'}, {'table', '04'},
                    {'memory', '05'}, {'global', '06'},
                    {'export', '07'}, {'start', '08'},
                    {'element', '09'}, {'code', '0a'},
                    {'data', '0b'}]
    section_code_dict = dict(section_code)


class CLIArgParser(object):
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--wasm", type=str,
                            help="path to the wasm test file")
        self.args = parser.parse_args()
        if self.args.wasm is None:
            raise Exception('empty wasm text file path')

    def getWASMTPath(self):
        return self.args.wasm


class WASMText(object):
    wast_header_type = dict()
    wast_header_import = dict()
    wast_header_table = dict()
    wast_header_elem = dict()
    wast_header_memory = dict()
    wast_header_data = dict()
    wast_header_export = dict()
    wast_header_func = dict()
    wast_func_bodies = dict()

    def __init__(self, file_path):
        self.wasmt_file = open(file_path, "r")
        self.file_path = file_path
        self.test_file = open("./test.txt", "a")

    def write(self, text):
        self.wasmt_file.write(text)

    def reopen_for_read(self):
        self.wasmt_file.close()
        self.wasmt_file.open(self.file_path, "r")

    def reopen_for_write(self):
        self.wasmt_file.close()
        self.wasmt_file.open(self.file_path, "w")

    def test_print(self):
        for line in self.wasmt_file:
            print(line, file=self.test_file)
            sys.stdout.write(line)
            sys.stdout.write('\n')

    def RegExSearch(self):
        # pattern1 = re.compile('^\(type\ \$[a-zA-Z0-9]+\$[v|i]+\ \(func$\)')
        pattern1 = re.compile('[ \t]+\(type.+\)')
        # pattern1 = re.compile('[a-zA-Z0-9]+')
        pattern2 = re.compile('[ \t]+\(import.+\)')
        pattern3 = re.compile('[ \t]+\(table.+\)')
        pattern4 = re.compile('[ \t]+\(elem.+\)')
        pattern5 = re.compile('[ \t]+\(memory.+\)')
        pattern6 = re.compile('[ \t]+\(data.+\)')
        pattern7 = re.compile('[ \t]+\(export.+\)')
        pattern8 = re.compile('[ \t]+\(func.+\)')

        linenumber = 0

        for line in self.wasmt_file:
            # print(line)
            linenumber += 1
            result = re.match(pattern1, line)
            if result is not None:
                self.wast_header_type[linenumber] = line
            result = re.match(pattern2, line)
            if result is not None:
                self.wast_header_import[linenumber] = line
            result = re.match(pattern3, line)
            if result is not None:
                self.wast_header_table[linenumber] = line
            result = re.match(pattern4, line)
            if result is not None:
                self.wast_header_elem[linenumber] = line
            result = re.match(pattern5, line)
            if result is not None:
                self.wast_header_memory[linenumber] = line
            result = re.match(pattern6, line)
            if result is not None:
                self.wast_header_data[linenumber] = line
            result = re.match(pattern7, line)
            if result is not None:
                self.wast_header_export[linenumber] = line
            result = re.match(pattern8, line)
            if result is not None:
                self.wast_header_func[linenumber] = line

    def FuncParser(self):
        parentheses_cnt = 0
        func_cnt = 0
        funcbody = str()
        pos = 0
        for key in self.wast_header_func:
            self.wasmt_file.seek(0, 0)
            parentheses_cnt = 0
            i = 0
            alive = False
            for line in self.wasmt_file:
                i += 1
                if i == key or alive:
                    func_cnt += 1
                    funcbody += line

                    pos = line.find('(', pos, len(line))
                    while(pos != -1):
                        parentheses_cnt += 1
                        pos = line.find('(', pos + 1, len(line))
                    pos = 0

                    pos = line.find(')', pos, len(line))
                    while(pos != -1):
                        parentheses_cnt -= 1
                        pos = line.find('(', pos + 1, len(line))
                    pos = 0

                    if parentheses_cnt == 0:
                        self.wast_func_bodies[func_cnt] = funcbody
                        func_cnt = 0
                        parentheses_cnt = 0
                        funcbody = ""
                        alive = False
                        break
                    elif parentheses_cnt > 0:
                        # we need to parse another line
                        alive = True
                        continue
                    else:
                        # parentheses_cnt < 0. the wasmt file is malformed.
                        raise Exception('malformed: mismatching number \
                                        of parentheses')

    def FuncParserTest(self):
        for k in self.wast_func_bodies:
            print(self.wast_func_bodies[k])

    def PrintTypeDict(self):
        for element in self.wast_header_type:
            # print(self.wast_header_type[element])
            print(Colors.OKGREEN + self.wast_header_type[element] + Colors.ENDC)

    def PrintImportDict(self):
        for element in self.wast_header_import:
            print(Colors.FAIL + self.wast_header_import[element] + Colors.ENDC)

    def PrintTableDict(self):
        for element in self.wast_header_table:
            print(Colors.HEADER + self.wast_header_table[element] + Colors.ENDC)

    def PrintElemDict(self):
        for element in self.wast_header_elem:
            print(Colors.OKBLUE + self.wast_header_elem[element] + Colors.ENDC)

    def PrintMemoryDict(self):
        for element in self.wast_header_memory:
            print(Colors.UNDERLINE + self.wast_header_memory[element] +
                  Colors.ENDC)

    def PrintDataDict(self):
        for element in self.wast_header_data:
            print(Colors.WARNING + self.wast_header_data[element] + Colors.ENDC)

    def PrintExportDict(self):
        for element in self.wast_header_export:
            print(Colors.BOLD + self.wast_header_export[element] + Colors.ENDC)

    def PrintFuncDict(self):
        for element in self.wast_header_func:
            print(Colors.HEADER + self.wast_header_func[element] + Colors.ENDC)

    def getTypeHeader(self):
        return self.wast_header_type

    def getImportHeader(self):
        return self.wast_header_import

    def getTableHeader(self):
        return self.wast_header_table

    def getElemHeader(self):
        return self.wast_header_elem

    def getMemoryHeader(self):
        return self.wast_header_memory

    def getDataHeader(self):
        return self.wast_header_data

    def getExportHeader(self):
        return self.wast_header_export

    def getFuncHeader(self):
        return self.wast_header_func

    def getFuncBodies(self):
        return self.wast_func_bodies

    def __del__(self):
        self.test_file.close()
        self.wasmt_file.close()


# i know the name is off-putting but this is technically our lexer.
class FuncBodyParser(object):
    wast_obj_func = dict()

    def __init__(self, wast_obj_func):
        self.wast_obj_func = wast_obj_func

    def ParseBody(self):
        pos = 0
        lastopenparen = 0

        for funcbody in self.wast_obj_func:
            for line in funcbody:
                parentheses_cnt = 0
                pos = line.find('(', pos, len(line))
                lastopenparen = pos
                while(pos != -1):
                    parentheses_cnt += 1
                    pos = line.find('(', pos + 1, len(line))
                    lastopenparen
                pos = 0

                pos = line.find(')', pos, len(line))
                while(pos != -1):
                    parentheses_cnt -= 1
                    pos = line.find('(', pos + 1, len(line))
                pos = 0

                if parentheses_cnt == 0:
                    parentheses_cnt = 0
                    break
                elif parentheses_cnt > 0:
                    # we need to parse another line
                    continue
                else:
                    # parentheses_cnt < 0. the wasmt file is malformed
                    print("goofball")

    def ParseBodyV2(self):
        sexpr_pattern = re.compile('\([^(]*?\)')

        for funcbody in self.wast_obj_func:
            print(Colors.OKBLUE + self.wast_obj_func[funcbody] + Colors.ENDC)

            most_concat_sexpr = re.findall(sexpr_pattern,
                                           self.wast_obj_func[funcbody])
            print ('-----------------------------')

            for elem in most_concat_sexpr:
                print(elem)
                print ('-----------------------------')
                elem.split

    def ParseBodyV3(self, Print):
        stack = []
        expr = []
        full = []
        sexpr_greedy = re.compile('\s*(?:(?P<lparen>\()|(?P<rparen>\))|(?P<operandnum>[i|ui][0-9]+$)|(?P<regarg>\$[0-9]+$)|(?P<keyword>[a-zA-Z0-9\._]+)|(?P<identifier>[\$][a-zA-Z0-9_\$]+))')

        for funcbody in self.wast_obj_func:
            for stackval in re.finditer(sexpr_greedy,
                                        self.wast_obj_func[funcbody]):
                for k, v in stackval.groupdict().items():
                    if Print:
                        if v is not None:
                            print(k, v)

                    if v is not None:
                        if k == 'rparen':
                            flag = True
                            expr.append(v)
                            while flag:
                                temp = stack.pop()
                                if temp is '(':
                                    flag = False
                                expr.append(temp)
                            full.append(expr)
                            expr = []
                        else:
                            stack.append(v)

        for val in full:
            print(val)
        return(full)


class WASM_CodeEmitter(object):
    Obj_file = []
    Obj_Header = []
    little_endian = True

    def __init__(self, stack):
        self.stack = stack

    def SetNewStack(self, new_stack):
        self.stack = new_stack

    def Obj_Header_32(self):
        magic_number = '0061736d'
        version = '01000000'

        self.Obj_file.append(magic_number)
        self.Obj_file.append(version)

    def EmitTypeHeader(self):
        val_cnt = 0
        byte_cnt = 0
        word = str()
        param_sentence = str()
        result_sentence = str()
        tmp_obj = []

        for stacks in self.stack:
            for stack_value in stacks:
                if stack_value in WASM_OP_Code.type_ops_dict:
                    if stack_value == 'func':
                        tmp_obj.append(WASM_OP_Code.type_ops_dict[stack_value])
                        if param_sentence != "":
                            tmp_obj.append(param_sentence)
                        else:
                            tmp_obj.append("00")
                            byte_cnt += 1

                        if result_sentence != "":
                            tmp_obj.append(result_sentence)
                        else:
                            tmp_obj.append("00")
                            byte_cnt += 1

                        param_sentence = ""
                        result_sentence = ""
                        val_cnt = 0
                    else:
                        word += WASM_OP_Code.type_ops_dict[stack_value]
                        val_cnt += 1
                    byte_cnt += 1
                elif stack_value == 'param':
                    param_sentence += str(bytes([val_cnt])) + word
                    byte_cnt += 1
                    val_cnt = 0
                    word = ""
                elif stack_value == 'result':
                    result_sentence += str(bytes([val_cnt])) + word
                    byte_cnt += 1
                    val_cnt = 0
                    word = ""

        tmp_obj.insert(0, '8080')
        tmp_obj.insert(0, format(byte_cnt, 'x'))
        # tmp_obj.insert(0, WASM_OP_Code.section_code_dict['type'])
        tmp_obj.insert(0, "01")
        # tmp_obj.insert(0, '01')
        self.Obj_Header = tmp_obj

    def PrintTypeHeaderObj(self):
        # print(self.Obj_Header)

        for byte in self.Obj_Header:
            print(byte)

    def Dump_Obj_STDOUT(self):
        for bytecode in self.Obj_file:
            print(bytecode)


class ParserV1(object):
    def run(self):
        argparser = CLIArgParser()
        wasmtobj = WASMText(argparser.getWASMTPath())
        # wasmtobj.test_print()
        wasmtobj.RegExSearch()
        if __DBG__:
            wasmtobj.PrintTypeDict()
            wasmtobj.PrintImportDict()
            wasmtobj.PrintTableDict()
            wasmtobj.PrintElemDict()
            wasmtobj.PrintMemoryDict()
            wasmtobj.PrintDataDict()
            wasmtobj.PrintExportDict()
            wasmtobj.PrintFuncDict()
            wasmtobj.PrintElemDict()
        wasmtobj.FuncParser()
        if __DBG__:
            wasmtobj.FuncParserTest()

        funcbodyparser = FuncBodyParser(wasmtobj.getFuncBodies())
        headerparser = FuncBodyParser(wasmtobj.getTypeHeader())

        expr_stack = funcbodyparser.ParseBodyV3(False)
        header_stack = headerparser.ParseBodyV3(True)

        wasm_codeemitter = WASM_CodeEmitter(expr_stack)
        wasm_codeemitter.Obj_Header_32()
        wasm_codeemitter.Dump_Obj_STDOUT()

        wasm_codeemitter.SetNewStack(header_stack)
        wasm_codeemitter.EmitTypeHeader()
        wasm_codeemitter.PrintTypeHeaderObj()


def main():
    parser = ParserV1()
    parser.run()


if __name__ == '__main__':
    main()
