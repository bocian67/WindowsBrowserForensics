from os import system, name


def parse_int_set(input_range=""):
    selection = list()
    invalid = list()
    # tokens are comma seperated values
    tokens = [x.strip() for x in input_range.split(',')]
    for i in tokens:
        try:
            # typically tokens are plain old integers
            selection.append(int(i))
        except:
            # if not, then it might be a range
            try:
                token = [int(k.strip()) for k in i.split('-')]
                if len(token) > 1:
                    token.sort()
                    # we have items seperated by a dash
                    # try to build a valid range
                    first = token[0]
                    last = token[len(token) - 1]
                    for x in range(first, last + 1):
                        selection.append(x)
            except:
                # not an int and not a range...
                invalid.append(i)
    return selection


def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')


class Menu:
    def __init__(self, title, selection_list, epilogue=""):
        self.title = title
        self.selection_list = selection_list
        self.epilogue = epilogue

    def show(self):
        print(self.title)
        for i in range(len(self.selection_list)):
            print(str(i) + "\t" + self.selection_list[i])
        selection = input(self.epilogue)
        clear()
        return parse_int_set(selection)
