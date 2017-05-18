import copy


class SymbolTable(list):
    temp_variable_counter = 0

    def __contains__(self, item):
        for symbol in self:
            if symbol["place"] == item:
                return True
        return False

    def index(self, object, start: int = 0, stop: int = ...):
        for i in range(0, len(self)):
            if self[i]["place"] == object:
                return i
        return -1

    def get_new_temp_variable(self, type):
        place = "T" + str(self.temp_variable_counter)
        self.temp_variable_counter += 1
        index = self.install_id(self.get_new_variable_dictionary(place))
        self[index]["declared"] = True
        self[index]["index"] = index
        self[index]["type"] = type
        return self[index]

    def get_new_variable_dictionary(self, place):
        return {"declared": False, "index": None,
                "is_array": False, "type": None, "place": place, "initializer": None}

    def install_id(self, identifier):
        self.append(identifier)
        return len(self) - 1

    def check_variable_declaration(self, variable, param):
        if not variable["declared"]:
            msg = "variable \'" + variable["place"] + "\' not declared!!"
            raise CompilationException(msg, param)


class CodeArray(list):
    def get_new_entry(self):
        return {"opt": None, "first_arg": None, "second_arg": None, "result": None, "label_used": None}

    def get_new_entry(self, opt, result, first_arg, second_arg, label_used):
        return {"opt": opt, "result": result, "first_arg": first_arg, "second_arg": second_arg,
                "label_used": label_used}

    def emit(self, opt, result, first_arg, second_arg):
        self.append(self.get_new_entry(opt, result, first_arg, second_arg, False))
        return

    def get_next_quad_index(self):
        return len(self)

    def get_current_quad_index(self):
        return len(self) - 1

    def create_simple_if_check(self, arg):
        starting_quad_index = code_array.get_next_quad_index()
        arg["t_list"] = [code_array.get_next_quad_index() + 1]
        arg["f_list"] = [code_array.get_next_quad_index() + 2]
        code_array.emit("if", None, arg, None)
        code_array.emit("goto", None, None, None)
        code_array.emit("goto", None, None, None)
        return starting_quad_index

    def backpatch_e_list(self, e_list, target):
        for quad_entry_index in e_list:
            code_array[quad_entry_index]["first_arg"] = target
        return

    def merge_e_lists(self, e_list_1, e_list_2):
        return e_list_1 + e_list_2

    def get_variable_string(self, variable):
        if variable is None:
            return None
        result = ""
        if "value" in variable:
            result = str(variable["value"])
        else:
            result = str(variable["place"])
            if variable["is_array"]:
                if "array_index" not in variable:
                    raise CompilationException("array \'" + variable["place"] + "\' without index!!!")
                else:
                    index_string = code_array.get_variable_string(variable["array_index"])
                    result += "[" + str(index_string) + "]"
        return result

    def initialize_variable(self, variable):
        if variable["is_array"]:
            code_array.emit("malloc", variable, None, None)
            if variable["initializer"] is not None:
                for i in range(0, len(variable["initializer"]["initial_value"])):
                    temp_variable = copy.deepcopy(variable)
                    temp_variable["array_index"] = {"value": i, "type": "int"}
                    code_array.emit("=", temp_variable, variable["initializer"]["initial_value"][i], None)
        elif variable["initializer"] is not None:
            code_array.emit("=", variable, variable["initializer"]["initial_value"][0], None)
        return

    def store_boolean_expression_in_variable(self, exp):
        if exp["type"] == "bool" and "place" not in exp and "value" not in exp:
            if "value" in exp:
                self.create_simple_if_check(exp)
            temp_var = symbol_table.get_new_temp_variable("bool")
            self.emit("=", temp_var, {"value": 1, "type": "bool"}, None)
            self.backpatch_e_list(exp["t_list"], self.get_current_quad_index())
            self.emit("goto", None, self.get_next_quad_index() + 2, None)
            self.emit("=", temp_var, {"value": 0, "type": "bool"}, None)
            self.backpatch_e_list(exp["f_list"], self.get_current_quad_index())
            exp = temp_var
        return exp

    def setup_array_variable(self, target_variable, index, variable_param):
        if not target_variable["is_array"]:
            raise CompilationException("non array variable \'" + target_variable["place"] + "\' with index!!",
                                       variable_param)
        var_copy = copy.deepcopy(target_variable)
        index = code_array.store_boolean_expression_in_variable(index)
        array_index_variable = symbol_table.get_new_temp_variable("int")
        code_array.emit("-", array_index_variable, index, var_copy["range"]["from"])
        var_copy["array_index"] = array_index_variable
        return var_copy

    def check_variable_is_not_array(self, variable, param):
        if variable["is_array"]:
            raise CompilationException("array \'" + variable["place"] + "\' without index!!!", param)
        return


class CodeGenerator:
    def __init__(self):
        self.number_of_indentation = 0
        self.should_indent = False
        self.result_code = ""

    def generate_code(self):
        for entry in code_array:
            if entry["opt"] == "goto" and entry["first_arg"] is not None:
                code_array[entry["first_arg"]]["label_used"] = True
        self.result_code = ""
        self.__add_to_result_code("#include <stdlib.h>")
        self.__add_to_result_code("#include <stdbool.h>")
        self.__add_to_result_code("#include <stdio.h>")
        self.__add_to_result_code("int main()")
        self.__add_to_result_code("{")
        self.number_of_indentation = 1
        self.__generate_variables()
        self.__generate_statements()
        self.__add_to_result_code("return 0;")
        self.number_of_indentation = 0
        self.__add_to_result_code("}")
        return self.result_code

    def __generate_variables(self):
        for entry in symbol_table:
            declaration_code = entry["type"] + " "
            if entry["is_array"]:
                declaration_code += "*"
            declaration_code += entry["place"]
            declaration_code += ";"
            self.__add_to_result_code(declaration_code)
        return

    def __generate_statements(self):
        for i in range(0, len(code_array)):
            entry = code_array[i]
            entry_code = ""
            if entry["label_used"]:
                entry_code += "label_" + str(i) + ": "
            opt = entry["opt"]
            ########################################################################################################
            if opt == "malloc":
                array_size = code_array.get_variable_string(entry["result"]["array_size"])
                entry_code += entry["result"]["place"] + " = (" + entry["result"]["type"] + "*) malloc(" + str(
                    array_size) + ");"
            ########################################################################################################
            elif opt == '+' or opt == '-' or opt == '*' or opt == '/' or opt == '%':
                arg1 = code_array.get_variable_string(entry["first_arg"])
                arg2 = code_array.get_variable_string(entry["second_arg"])
                entry_code += entry["result"]["place"] + " = (" + entry["first_arg"]["type"] + ") " + str(
                    arg1) + " " + opt + " " + str(
                    arg2) + ";"
            ########################################################################################################
            elif opt == '=':
                arg1 = code_array.get_variable_string(entry["first_arg"])
                entry_code += code_array.get_variable_string(entry["result"]) + " = (" + entry["first_arg"][
                    "type"] + ") " + str(arg1) + ";"
            ########################################################################################################
            elif opt == '<' or opt == '<=' or opt == '>' or opt == '>=' or opt == '==' or opt == '!=':
                arg1 = code_array.get_variable_string(entry["first_arg"])
                arg2 = code_array.get_variable_string(entry["second_arg"])
                entry_code += "if (" + str(arg1) + " " + opt + " " + str(arg2) + ")"
                self.should_indent = True
            ########################################################################################################
            elif opt == 'goto':
                if self.should_indent:
                    entry_code += "\t"
                    self.should_indent = False
                entry_code += "goto label_" + str(entry["first_arg"]) + ";"
            ########################################################################################################
            elif opt == 'if':
                arg1 = code_array.get_variable_string(entry["first_arg"])
                entry_code += "if (" + str(arg1) + ")"
                self.should_indent = True
            ########################################################################################################
            elif opt == 'print':
                arg1 = code_array.get_variable_string(entry["first_arg"])
                char_type = "%d"
                if entry["first_arg"]["type"] == "char":
                    char_type = "%c"
                entry_code += "printf(\"" + char_type + "\", " + arg1 + ");"
            else:
                entry_code += str(entry)
            self.__add_to_result_code(entry_code)
        return

    def __add_indentations(self):
        for i in range(0, self.number_of_indentation):
            self.result_code += "\t"
        return

    def __add_to_result_code(self, code):
        self.__add_indentations()
        self.result_code += code + "\n"


class CompilationException(Exception):
    def __init__(self, msg, params=None):
        if params is not None:
            msg += "\tline: " + str(params.lineno)
        self.msg = msg
        Exception.__init__(self, msg)
        return


symbol_table = SymbolTable()
code_array = CodeArray()
