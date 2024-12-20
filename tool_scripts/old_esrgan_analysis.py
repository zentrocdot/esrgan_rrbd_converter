#!/usr/bin/python3
'''Analysis of the old ESRGAN data structure.'''
# pylint: disable=protected-access
# pylint: disable=useless-return
# pylint: disable=bare-except
# pylint: disable=invalid-name
# pylint: disable=consider-using-f-string
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=redefined-outer-name
# pylint: disable=pointless-statement
# pylint: disable=assignment-from-none
#
# old ESRGAN Model Data Analysis
# Version 0.0.0.2
#
# Description:
# Th script is working on base of the ESRGAN models
# I have worked with and I have seen so far.
#
# To-Do:
# Sanitize and optimise script.

# Import standard Python modules.
import re
import os
import sys
import warnings
from collections import OrderedDict

# Import third party module.
import torch

# Ignore (torch) future warning.
warnings.simplefilter(action='ignore', category=FutureWarning)

# Get the model name from the command line.
# To-Do: check if it is a pt or pth file.
if len(sys.argv) > 1:
    model_name = sys.argv[1]
else:
    exit_message = "No model on the command line given. Bye!"
    print(exit_message)
    os._exit(1)

# Define the color escape sequence strings.
COL_DEFAULT = "\33[49m"
COL_RED = "\33[41m"
COL_GREEN = "\33[42m"
COL_YELLOW = "\33[43m"
COL_BLUE = "\33[44m"
COL_MAGENTA = "\33[45m"
COL_CYAN = "\33[46m"
COL_GRAY = "\33[47m"
COL_DARK_GRAY = "\33[100m"

# Set some strings.
ERR_STR = "\n\33[41mERROR: Check the data structure!\33[49m"
WARN_STR_0 = "\n\33[46mFound UNKNOWN (OLD) ESRGAN RRBD model. Check the data!\33[49m"
WARN_STR_1 = "\n\33[46mFound UNKNOWN (NEW) ESRGAN RRBD model. Check the data!\33[49m"
INFO_STR_0 = "\n\33[45mFound old ESRGAN RRBD model data\33[49m"
INFO_STR_1 = "\n\33[45mFound new ESRGAN RRBD model data\33[49m"

# Set some strings.
WEIGHT_STR_0 = 'model.0.weight'
BIAS_STR_0 = 'model.0.bias'
WEIGHT_STR_1 = 'conv_first.weight'
BIAS_STR_1 = 'conv_first.bias'

# Define the regular expressions.
body_regex = r"^model.1.sub.\b([0-9]|[1][3-9]|[12][0-2])\b.RDB[1-3].conv[0-5].0.(?:weight|bias)$"
head_foot_regex = r"^model.(1.sub.23|[01368]+[0]*).(?:weight|bias)$"

# Compile the regular expressions for use.
pattern_body = re.compile(body_regex)
pattern_head_foot = re.compile(head_foot_regex)

# Set keyword dict and keyword list.
keyword_dict = {"RRDB_trunk.0.": "NEW ESRGAN",
                "model.1.sub.": "OLD ESRGAN",
                "body.": "RealESRGAN"}
keyword_list = list(keyword_dict.keys())

# Set pre/post tensor dict and pre/post string list.
ppdict = {"model.0.weight": [64, 3, 3, 3], "model.0.bias": [64],
          "model.1.sub.23.weight": [64, 64, 3, 3], "model.1.sub.23.bias": [64],
          "model.3.weight": [64, 64, 3, 3], "model.3.bias": [64],
          "model.6.weight": [64, 64, 3, 3], "model.6.bias": [64],
          "model.8.weight": [64, 64, 3, 3], "model.8.bias": [64],
          "model.10.weight": [3, 64, 3, 3], "model.10.bias": [3]}
pplist = list(ppdict.keys())

# New approach.
conv_tens = {"conv1": {"weight": [32, 64, 3, 3], "bias": [32]},
             "conv2": {"weight": [32, 96, 3, 3], "bias": [32]},
             "conv3": {"weight": [32, 128, 3, 3], "bias": [32]},
             "conv4": {"weight": [32, 160, 3, 3], "bias": [32]},
             "conv5": {"weight": [64, 192, 3, 3], "bias": [64]}}

# Set model, weight and bias pattern.
PAT_W = "weight"
PAT_B = "bias"
PAT_MOD = "model"

# ++++++++++++++++++++++++
# Class clear_reset_term()
# ++++++++++++++++++++++++
class clear_reset_term():
    '''Clear and reset the terminal window.'''
    def __init__(self):
        '''Class __init__ function.'''
        self.esc_reset = "\33c"
        self.esc_clear = "\33[2J\33[H"

    def reset_term(self) -> None:
        '''Reset the terminal window.'''
        sys.stdout.write(self.esc_reset)
        sys.stdout.flush()
        return None

    def clear_term(self) -> None:
        '''Clear the terminal window.'''
        sys.stdout.write(self.esc_clear)
        sys.stdout.flush()
        return None

# Instantiate the methods of the clear reset class.
clear = clear_reset_term().clear_term()
reset = clear_reset_term().reset_term()

# --------------------
# Function load_data()
# --------------------
def load_data(filename):
    '''Load model data.'''
    # Try to load the model data from the file.
    # Must be of type collections.OrderedDict.
    try:
        model_content = torch.load(filename)
    except:
        err_str = "Could not load model data from file! Maybe not a valid model!"
        err_msg = "{0}{1}{2}".format(COL_RED, err_str, COL_DEFAULT)
        print(err_msg)
        model_content = None
    # Return model content.
    return model_content

# --------------------
# Function file_type()
# Magic Numbers Zip Files:
# PK\x03\x04
# PK\x05\x06 (empty)
# PK\x07\x08
# PK = \x50\x4B
# --------------------
def file_type(filename):
    '''Get file type.'''
    file_type = "unknown"
    with open(filename, 'rb') as file:
        content = file.read(2)
        if content.find(b'\x80\x02') != -1:
            file_type = "binary"
        elif content.find(b'\x50\x4B') != -1:
            file_type = "zip"
    # Return the file type.
    return file_type

# ---------------------
# Function check_keys()
# ---------------------
def check_keys(data):
    '''Check keys in model.'''
    # Declare the local variables and the array.
    ret_val = False
    ret_arr = []
    key_count = 0
    # Loop over the keys of the model.
    for key in data:
        # Add key to array and increment the key counter.
        ret_arr.append(key)
        key_count += 1
        if key.startswith(PAT_MOD):
            test = re.match(pattern_body, key)
            if test:
                ret_arr.remove(key)
            else:
                test = re.match(pattern_head_foot, key)
                if test:
                    ret_arr.remove(key)
    # On no mismatch set True.
    if not ret_arr:
        ret_val = True
    # Return True/False and mismatching data.
    return ret_val, ret_arr, key_count

# ------------------------
# Function check_tensors()
# ------------------------
def check_tensors(data):
    '''Check keys.'''
    # Initialise some variables.
    ret_val = False
    ret_arr = []
    body_count = 0
    # Loop over the keys of the dict.
    for key in data:
        if key.startswith(PAT_MOD) and key not in pplist:
            body_count += 1
            ret_arr.append(key)
            for k, v in conv_tens.items():
                if k in key and PAT_W in key and \
                    list(data[key].size()) == v[PAT_W]:
                    ret_arr.remove(key)
                    break
                if k in key and PAT_B in key and \
                    list(data[key].size()) == v[PAT_B]:
                    ret_arr.remove(key)
                    break
    # On no mismatch set True.
    if not ret_arr:
        ret_val = True
    # Return True/False and mismatching data.
    return ret_val, ret_arr, body_count

# ------------------------
# Function check_pre_pos()
# ------------------------
def check_pre_pos(data):
    '''Check pre and post key/value pairs.'''
    # initialise the return variables.
    ret_val = False
    ret_arr = []
    pp_count = 0
    # Loop over the keys of the data dict.
    for key in data:
        if key.startswith(PAT_MOD) and key in pplist:
            pp_count += 1
            ret_arr.append(key)
            # If key and tensor are correct remove key from array.
            if PAT_W in key:
                for k, v in ppdict.items():
                    if key == k and list(data[key].size()) == v:
                        ret_arr.remove(key)
                        break
            # If key and tensor are correct remove key from array.
            if PAT_B in key:
                for k, v in ppdict.items():
                    if key == k and list(data[key].size()) == v:
                        ret_arr.remove(key)
                        break
    # On no mismatch set True.
    if not ret_arr:
        ret_val = True
    # Return True/False and mismatching data.
    return ret_val, ret_arr, pp_count

# -----------------------
# Function check_esrgan()
# -----------------------
def check_esrgan(model_data, model):
    '''Main script function'''
    # Perform some checks.
    msg_str = "{0}{1}".format("\n", "***  key and tensor checks  ***")
    print(msg_str)
    chkval0, chkarr0, cnt0 = check_keys(model_data)
    chkval1, chkarr1, cnt1 = check_tensors(model_data)
    chkval2, chkarr2, cnt2 = check_pre_pos(model_data)
    # Print not empty arrays.
    if chkarr0:
        print("\n{}".format(chkarr0))
    else:
        print("\nKey check ok. Nothing to print out!")
    if chkarr1:
        print("\n{}".format(chkarr1))
    else:
        print("\nTensor check ok. Nothing to print out!")
    if chkarr2:
        print("\n{}".format(chkarr2))
    else:
        print("\nPre/Post key check ok. Nothing to print out!")
    # Check on mismatching lengths.
    if len(chkarr0) != cnt0 and len(chkarr0) > 0:
        print("\nMismatch in number of keys!")
        print(len(chkarr0), " wrong of ", cnt0)
    if len(chkarr1) != cnt1 and len(chkarr1) > 0:
        print("\nMismatch in number of body lines!")
        print(len(chkarr1), " wrong of ", cnt1)
    if len(chkarr2) != cnt2 and len(chkarr2) > 0:
        print("\nMismatch in number of pre/post keys!")
        print(len(chkarr2), " wrong of ", cnt2)
    if (chkval0 and chkval1 and chkval2) is True:
        info_str = "Old ESRGAN RRBD model. Perfekt match in the data structure."
        info_msg = "\n{0}{1}{2}".format(COL_GREEN, info_str, COL_DEFAULT)
        print(info_msg)
    elif (chkval0 and chkval1 and chkval2) is False:
        err_str = "NOT an Old ESRGAN RRBD model. No match in the data structure."
        err_msg = "\n{0}{1}{2}".format(COL_RED, err_str, COL_DEFAULT)
        print(err_msg)
    else:
        warn_str = "Maybe an Old ESRGAN RRBD model. Check the data!"
        warn_msg = "\n{0}{1}{2}".format(COL_YELLOW, warn_str, COL_DEFAULT)
        print(warn_msg)
    # Print comment.
    if model == "RealESRGAN":
        warn_str = "Take a look at the data structure. Maybe it is a RealESRGAN model!"
        warn_msg = "\n{0}{1}{2}".format(COL_CYAN, warn_str, COL_DEFAULT)
        print(warn_msg)
    # Return None
    return None

# ---------------------
# Function print_keys()
# ---------------------
def print_keys(model_content):
    '''Print keys from the model dict.'''
    # Print message into the terminal window.
    msg_str = "{0}{1}{2}".format("\n", "***  keys and tensor shapes  ***", "\n")
    print(msg_str)
    # Loop over they keys and print keyes ans tensor shape.
    for key in model_content:
        dim = list(model_content[key].size())
        print("%-35s%s" % (key, dim))
    # Return None.
    return None

# -------------------------
# Function get_model_type()
# -------------------------
def get_model_type(model_content) -> None:
    '''Get model type.'''
    # Loop over the keys in the model data.
    for key in model_content:
        # Loop over the keyword list.
        for k in keyword_list:
            # If keyword is in string print model type.
            if k in key:
                print("\n***  model type prediction  ***\n")
                print("Possible model type:", keyword_dict[k])
                break
        else:
            continue
        break
    # Return None.
    return None

# --------------------------
# Function model_data_type()
# --------------------------
def model_data_type(data) -> str:
    '''Get data type dict or OrderedDict.'''
    # Initialise the return type variable.
    ret_type = None
    # Get data type (dict or OrderedDict)
    if isinstance(data, OrderedDict):
        ret_type = "OrderedDict"
    elif isinstance(data, dict):
        ret_type = "dict"
    # Return None or data type.
    return ret_type

# ---------------------
# Function main_check()
# ---------------------
def main_check(data_type: str, model_content: dict|OrderedDict) -> OrderedDict:
    '''Main check of model data.'''
    # Declare model.
    model = None
    # Do something on data type.
    if  data_type == "OrderedDict":
        get_model_type(model_content)
        model = "ESRGAN"
    elif data_type == "dict":
        get_model_type(model_content)
        key_var = list(model_content.keys())[0]
        # Check the (possibly) single key in the dict.
        if key_var not in ("params_ema", "params"):
            msg_str = "{0}{1}{2}".format("\n", "***  new key word  ***", "\n")
            print(msg_str)
        else:
            msg_str = "{0}{1}{2}".format("\n", "***  known key word  ***", "\n")
            print(msg_str)
        print("Key word:", key_var)
        # Loop over the keyword list. Identify model this way.
        for keyword in keyword_list:
            if keyword in model_content[key_var]:
                print("Possible model type:", keyword_dict[keyword])
        # Look for the known and valid keywords.
        if key_var in ("params_ema", "params"):
            warn_str = "\nTake a look at the data structure. Maybe it is a RealESRGAN model!"
            warn_msg = "{0}{1}{2}".format(COL_CYAN, warn_str, COL_DEFAULT)
            print(warn_msg)
            model_content = model_content[key_var]
            model = "RealESRGAN"
        else:
            warn_str = "\nUnknown model type. Take a look at the data structure!"
            warn_msg = "{0}{1}{2}".format(COL_CYAN, warn_str, COL_DEFAULT)
            print(warn_msg)
            model = "UnknownESRGAN"
    else:
        err_str = "\nCould not find the correct data structure (dict/OrderedDict)!" + \
                  "Not a valid model!"
        err_msg = "{0}{1}{2}".format(COL_RED, err_str, COL_DEFAULT)
        print(err_msg)
        model = "Unknown"
    # Return model content.
    return model_content, model

# -----------------------
# Function simple_check()
# -----------------------
def simple_check(model_content):
    '''Simple check.'''
    # Perform some sipmple checks.
    isOLDW = None
    isOLDB = None
    isNEWW = None
    isNEWB = None
    weight_shape_ref = [64, 3, 3, 3]
    bias_shape_ref = [64]
    for key in model_content:
        # Check on old.
        if WEIGHT_STR_0 == key:
            weight_shape = list(model_content[WEIGHT_STR_0].size())
            isOLDW = bool(weight_shape == weight_shape_ref)
        if BIAS_STR_0 == key:
            bias_shape = list(model_content[BIAS_STR_0].size())
            isOLDB = bool(bias_shape == bias_shape_ref)
        # Check on new.
        if WEIGHT_STR_1 == key:
            weight_shape = list(model_content[WEIGHT_STR_1].size())
            isNEWW = bool(weight_shape == weight_shape_ref)
        if BIAS_STR_1 == key:
            bias_shape = list(model_content[BIAS_STR_1].size())
            isNEWB = bool(bias_shape == bias_shape_ref)
    # Check the possible cases.
    if isOLDW and isOLDB is not None and bool(isOLDW == isOLDB):
        print(INFO_STR_0)
    elif isNEWW and isNEWB is not None and bool(isNEWW == isNEWB):
        print(INFO_STR_1)
    elif isOLDW or isOLDB is not None and bool(isOLDW == isOLDB):
        print(WARN_STR_0)
    elif isNEWW or isNEWB is not None and bool(isOLDW == isOLDB):
        print(WARN_STR_1)
    else:
        print(model_content)
        print(ERR_STR)
    # Return None
    return None

# ++++++++++++++++++++
# Main script function
# ++++++++++++++++++++
def main(filename):
    '''Main script function'''
    # Print file type for analysis purposes.
    msg_str = "{0}{1}".format("***  file type  ***", "\n")
    print(msg_str)
    print("File type:", file_type(filename))
    # Load the model data.
    model_content = load_data(filename)
    # Leave function on None.
    if model_content is None:
        return None
    # Check if model structure is dict or OrderedDict.
    msg_str = "{0}{1}{2}".format("\n", "***  data type  ***", "\n")
    print(msg_str)
    data_type = model_data_type(model_content)
    print("Data type:", data_type)
    # Main check of model data.
    model_content, model = main_check(data_type, model_content)
    # Print model keys.
    if model in ("ESRGAN", "RealESRGAN"):
        print_keys(model_content)
    # Call check function.
        check_esrgan(model_content, model)
    # Simple check.
    if model in ("ESRGAN"):
        simple_check(model_content)
    # Return None
    return None

# Execute as module as well as a program.
if __name__ == "__main__":
    # Reset the terminal window.
    reset
    # Call the main function.
    main(model_name)
