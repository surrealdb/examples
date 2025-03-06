import numpy as np
import re

PUNCTUATION_TO_SEPARATE = [
                ".", ",", "?", "!", ";", ":", "(", ")", "[", "]", "{", "}", "\"", "'", "`", "/", "\\", "<", ">", "—", "–"
            ]

class WordEmbeddingModel:
    

    def __init__(self,model_path):
        self.dictionary = {}
        self.vector_size = 0
        self.model_path = model_path

        with open(self.model_path, 'r', encoding='utf-8') as f:
            for line in f:
                values = line.split()
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
