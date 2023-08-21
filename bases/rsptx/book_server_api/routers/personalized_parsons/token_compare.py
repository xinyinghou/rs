import difflib
import tokenize
import io
"""
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
openai.api_key = ""

def get_embedding(code):
    embedding = openai.Embedding.create(
        model="text-embedding-ada-002",
        input= buggy_code
            )
    return embedding["data"][0]["embedding"]


def get_similarity_code(buggy_code, fixed_code):
    
    # Convert the lists of embeddings to NumPy arrays
    # Reshape the arrays to be 2D (n_samples, n_features)

    buggy_code_embedding = np.array(get_embedding(buggy_code)).reshape(1, -1)
    fixed_code_embedding = np.array(get_embedding(fixed_code)).reshape(1, -1)

    # Convert the list of embeddings to a NumPy array
    # Calculate cosine similarity between the embeddings
    similarity_matrix = cosine_similarity(buggy_code_embedding, fixed_code_embedding)
    average_cosine_similarity = np.mean(similarity_matrix)

    return average_cosine_similarity


buggy_code = "def has22(nums):\n    flag = 0\n    for num in nums:\n        if num == 2 and flag == 0:\n            flag = 1\n            return True\n        elif num != 2:\n            flag = 0\n            return False "
fixed_code = "def has22(nums):\n    flag = 0\n    for num in nums:\n        if num == 2 and flag == 1:\n            return True\n        elif num == 2:\n            flag = 1\n        elif num != 2:\n            flag = 0\n    return False"
common_code = "def has22(nums):\n    for i in range(len(nums)-1):\n        if nums[i]==2 and nums[i+1]==2:\n            return True\n    return False"

print("len",len(buggy_code), len(fixed_code),len(common_code))
# Tokenize code lines into words
similarity_personalized = difflib.SequenceMatcher(None, buggy_code.split(), fixed_code.split()).ratio()
similarity_most_common = difflib.SequenceMatcher(None, buggy_code.split(), common_code.split()).ratio()
"""
def normalize_indentation(code):
    lines = code.split('\n')
    normalized_lines = [line.lstrip() for line in lines]
    return '\n'.join(normalized_lines)


def code_similarity_score(code1, code2):
    # Tokenize code snippets using ASTTokens
        # Tokenize code snippets using the tokenize module
    tokens1 = [token.string for token in tokenize.tokenize(io.BytesIO(normalize_indentation(code1).encode('utf-8')).readline)]
    tokens2 = [token.string for token in tokenize.tokenize(io.BytesIO(normalize_indentation(code2).encode('utf-8')).readline)]

    # Create a SequenceMatcher object
    matcher = difflib.SequenceMatcher(None, tokens1, tokens2)

    similarity_ratio = matcher.ratio()

    return similarity_ratio

#code1 = "for i in range(0,len(tuple_list)):"
#code2 = "for i in range(0,len(tuple_list)-1):"

#print(code_similarity_score(code1, code2))