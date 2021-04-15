import pycrfsuite

import recipe_crf_model_data_prep as prep
import recipe_crf_model_training as train

def sentence_predict_label(sentence, model_path):    
    recipe_input_crf_format = prep.sentence_format_for_crf(sentence)    
    recipe_input_token = recipe_input_crf_format[0]
    
    tagger = pycrfsuite.Tagger()
    tagger.open(model_path)  
    
    return tagger.tag(train.sentence_to_features(recipe_input_token))

def format_prediction(sentence, prediction_output):
    sentence_clean = prep.sentence_clean_input(sentence)    
    sentence_list = prep.sentence_to_list(sentence_clean)
    prediction_dict = {}
    for element, label in zip(sentence_list, prediction_output):        
        prediction_dict[element] = label    
    return prediction_dict

def get_name_from_prediction(prediction_formatted):
    names = [k for k,v in prediction_formatted.items() if v == 'NAME']
    names_formatted = ' '.join(names)
    return names_formatted

def get_qty_from_prediction(prediction_formatted):
    qty = [k for k,v in prediction_formatted.items() if v == 'QTY']
    #qty_formatted = '|'.join(qty)
    if len(qty) > 0:
        qty_formatted = qty[0] # If multiple units, returns only first
    else:
        qty_formatted = ''.join(qty)
    return qty_formatted

def get_unit_from_prediction(prediction_formatted):
    units = [k for k,v in prediction_formatted.items() if v == 'UNIT']
    #units_formatted = '|'.join(units)
    if len(units) > 0:
        units_formatted = units[0] # If multiple units, returns only first
    else:
        units_formatted = ''.join(units)
    return units_formatted        

recipe_input_raw = "1 egg, beaten with 1 tablespoon water, for egg wash"
print(prep.sentence_format_for_crf(recipe_input_raw))
prediction = sentence_predict_label(recipe_input_raw,"models/recipetagging-v5.crfsuite" )

formatted = format_prediction(recipe_input_raw, prediction)

print(formatted)
# print(get_name_from_prediction(formatted))
# print(get_unit_from_prediction(formatted))
# print(get_qty_from_prediction(formatted))


# recipe_input_raw = "3 radishes, cleaned and thinly sliced"
# recipe_input_crf_format = prep.sentence_format_for_crf(recipe_input_raw)
# recipe_input_token = recipe_input_crf_format[0]
# print(recipe_input_token)
# prediction_output = sentence_predict_label(recipe_input_token, 'recipetagging-v2.crfsuite')

# print("Full ingredient is: " + recipe_input_raw)
# for input, prediction in zip(recipe_input_token, prediction_output):
#     print("Ingredient Element: " + str(input[0]) + "   Classification: ", str(prediction))
