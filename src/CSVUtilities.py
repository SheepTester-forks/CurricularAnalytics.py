from typing import List, Literal, Union


def readfile(file_path: str) -> List[str]:
    with open(file_path) as f:
        return f.readlines()


def remove_empty_lines(file_path: str) -> Union[str, Literal[False]]:
    if file_path[-4:] != ".csv":
        print("Input is not a csv file")
        return False
    temp_file = file_path[:-4] + "_temp.csv"
    file = readfile(file_path)
    with open(temp_file, "w") as f:
        new_file = ""
        for line in file:
            line = line.replace("\r", "")
            if len(line) > 0 and not line.replace('"', "").startswith("#"):
                line = line + "\n"
                new_file = new_file + line
        if len(new_file) > 0:
            new_file = new_file[:-1]
        f.write(new_file)
    return temp_file
