import numpy as np
import re

PUNCTUATION_TO_SEPARATE = [
                ".", ",", "?", "!", ";", ":", "(", ")", "[", "]", "{", "}", "\"", "'", "`", "/", "\\", "<", ">", "—", "–"
            ]

class WordEmbeddingModel:
    
    # Preprocess token text
    staticmethod
    def process_token_text_for_txt_file(text:str) ->str:
        token = str(text).lower()
        token = re.sub(r'[^\w\s]', '', token)  # Remove punctuation
        token = re.sub(r'\s+', ' ', token)  # Normalize whitespace (replace multiple spaces, tabs, newlines with a single ' ')
        token = token.strip()
        token = token.replace(" ","!") # escape character should be no punctuation
        return token
    
    
    # Preprocess token text (example - adjust as needed)
    staticmethod
    def unescape_token_text_for_txt_file(text:str) ->str:
        if text:
            return text.replace("!"," ") # unescape to get back the space
        else:
            return ""



    def __init__(self,model_path,unescape_words:False):
        self.dictionary = {}
        self.vector_size = 0
        self.model_path = model_path

        with open(self.model_path, 'r', encoding='utf-8') as f:
            for line in f:
                values = line.split()
                if unescape_words:
                    word = WordEmbeddingModel.unescape_token_text_for_txt_file(values[0])
                else:
                    word = values[0]
                vector = np.asarray(values[1:], "float32")
                self.dictionary[word] = vector
                if self.vector_size==0:
                    self.vector_size = len(vector)


    def separate_punctuation(sentence):
        """Separates specified punctuation characters with a space before them."""
        punctuation_regex = re.compile(r"([{}])".format(re.escape("".join(PUNCTUATION_TO_SEPARATE))))
        return punctuation_regex.sub(r" \1", sentence)

    
    #This method will generate an embedding for a piece of text
    def sentence_to_vec(self,sentence):

        words = WordEmbeddingModel.separate_punctuation(sentence).lower().split()
        
        vectors = [self.dictionary[w] for w in words if w in self.dictionary]

        if vectors:
            return np.mean(vectors, axis=0).tolist()
        else:
            return np.zeros(self.vector_size).tolist()
