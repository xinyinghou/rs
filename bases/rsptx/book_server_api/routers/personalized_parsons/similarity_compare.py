import torch
from transformers import RobertaModel, RobertaTokenizer
import torch.nn.functional as F
import pandas as pd

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
model = RobertaModel.from_pretrained("microsoft/codebert-base")
model.to(device)

def get_similarity_code(buggy_code, fixed_code):
    
    tokenized_input = tokenizer([buggy_code, fixed_code], truncation=True, padding=True, return_tensors="pt")
        #no gradient calculation - do not want to change the paras in the model

    with torch.no_grad():
        # last_hidden_state: sequence of hidden-states at the output of the last layer of the model.
        encoded_input = model(**tokenized_input).last_hidden_state
        encoded_input = torch.mean(encoded_input, dim=1)
    # Normalize the encoded vectors
    # p: the exponent value in the norm formulation.
    # dim: the dimension to reduce

    # CodeBERT:
    # Weuse Transformer with 6 layers,768 dimensional hidden states and 12 attention heads as our decoder in all settings.
    normalized_input = F.normalize(encoded_input, p=2, dim=1)
    # Compute cosine similarity
    similarity = F.cosine_similarity(normalized_input[0].unsqueeze(0), normalized_input[1].unsqueeze(0),dim=1)
    
    return similarity.item()


buggy_code = "def has22(nums):\n    flag = 0\n    for num in nums:\n        if num == 2 and flag == 0:\n            flag = 1\n            return True\n        elif num != 2:\n            flag = 0\n            return False"
fixed_code = "def has22(nums):\n    flag = 0\n    for num in nums:\n        if num == 2 and flag == 1:\n            return True\n        elif num == 2:\n            flag = 1\n        elif num != 2:\n            flag = 0\n    return False"
common_code = "def has22(nums):\n    for i in range(len(nums)-1):\n        if nums[i]==2 and nums[i+1]==2:\n            return True\n    return False"

print(get_similarity_code(buggy_code, fixed_code))
print(get_similarity_code(buggy_code, common_code))