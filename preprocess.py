import sg_utils
import numpy as np
from collections import Counter
from pycocotools.coco import COCO
import code
import copy

def get_vocab_top_k(vocab, k):
  v = dict();
  for key in vocab.keys():
    v[key] = vocab[key][:k]
  return v

def get_vocab_counts(image_ids, coco_caps, max_cap, vocab):
  #this import is placed here so that people who do not wish to install nltk can skip it
  from nltk import pos_tag, word_tokenize
  counts = np.zeros((len(image_ids), len(vocab['words'])), dtype = np.float)
  wordMap = {};
  for x in range(len(vocab['words'])):
    wordMap[vocab['words'][x]] = x;

  for i in xrange(len(image_ids)):
    ann_ids = coco_caps.getAnnIds(image_ids[i])
    assert(len(ann_ids) >= max_cap), 'less than {:d} number of captions for image {:d}'.format(max_cap, image_ids[i])
    ann_ids.sort()
    ann_ids = ann_ids[:max_cap]
    anns = coco_caps.loadAnns(ann_ids)
    tmp = [word_tokenize( str(a['caption']).lower()) for a in anns]
    for (j,tmp_j) in enumerate(tmp):
      pos = [wordMap[tmp_j_k] for tmp_j_k in tmp_j if tmp_j_k in wordMap]
      pos = list(set(pos))
      counts[i, pos] = counts[i,pos]+1
  return counts

def get_vocab_counts(image_ids, coco_caps, vocab, simpleToken=False):
  #this import is placed here so that people who do not wish to install nltk can skip it
  from nltk import pos_tag, word_tokenize
  counts = np.zeros((len(image_ids), len(vocab['words'])), dtype = np.float)
  wordMap = {};
  for x in range(len(vocab['words'])):
    wordMap[vocab['words'][x]] = x;

  for i in xrange(len(image_ids)):
    ann_ids = coco_caps.getAnnIds(image_ids[i]) 
    ann_ids.sort()    
    anns = coco_caps.loadAnns(ann_ids)
    #try:
    if simpleToken:
      tmp = [str(a['caption'].encode('ascii','ignore')).lower().split(' ') for a in anns]
    else:
      tmp = [word_tokenize( str(a['caption'].encode('ascii','ignore')).lower()) for a in anns]

    for (j,tmp_j) in enumerate(tmp):
      pos = [wordMap[tmp_j_k] for tmp_j_k in tmp_j if tmp_j_k in wordMap]
      pos = list(set(pos))
      counts[i, pos] = counts[i,pos]+1
  return counts  


def merge_pos(orig_vocab):
  mapping = {'NNS': 'NN', 'NNP': 'NN', 'NNPS': 'NN', 'NN': 'NN', \
  'VB': 'VB', 'VBD': 'VB', 'VBN': 'VB', 'VBZ': 'VB', 'VBP': 'VB', 'VBP': 'VB', 'VBG': 'VB', \
  'JJR': 'JJ', 'JJS': 'JJ', 'JJ': 'JJ', 'DT': 'DT', 'PRP': 'PRP', 'PRP$': 'PRP', 'IN': 'IN'};
  vocab = copy.deepcopy(orig_vocab);
  for ind, p in enumerate(vocab['poss']):
    if p in mapping:
      vocab['poss'][ind] = mapping[p];
    else:
      vocab['poss'][ind] = 'other';
  return vocab;

def get_vocab(imset, coco_caps, punctuations, mapping):
  #this import is placed here so that people who do not wish to install nltk can skip it
  from nltk import pos_tag, word_tokenize
  image_ids = coco_caps.getImgIds()
  image_ids.sort(); t = []

  for i in xrange(len(image_ids)):
    annIds = coco_caps.getAnnIds(image_ids[i]);
    anns = coco_caps.loadAnns(annIds);
    tmp = [pos_tag( word_tokenize( str(a['caption']).lower())) for a in anns]
    t.append(tmp)

  # Make a vocabulary by computing counts of words over the whole dataset.
  t = [t3 for t1 in t for t2 in t1 for t3 in t2]
  t = [(l, 'other') if mapping.get(r) is None else (l, mapping[r]) for (l,r) in t]
  vcb = Counter(elem for elem in t)
  vcb = vcb.most_common()

  # Merge things that are in the same or similar pos
  word = [l for ((l,r),c) in vcb];
  pos = [r for ((l,r),c) in vcb];
  count = [c for ((l,r),c) in vcb];

  poss = [];
  counts = [];
  words = sorted(set(word))
  for j in xrange(len(words)):
    indexes = [i for i,x in enumerate(word) if x == words[j]]
    pos_tmp = [pos[i] for i in indexes]
    count_tmp = [count[i] for i in indexes]
    ind = np.argmax(count_tmp)
    poss.append(pos_tmp[ind])
    counts.append(sum(count_tmp))

  ind = np.argsort(counts)
  ind = ind[::-1]
  words = [words[i] for i in ind]
  poss = [poss[i] for i in ind]
  counts = [counts[i] for i in ind]

  # Remove punctuations
  non_punct = [i for (i,x) in enumerate(words) if x not in punctuations]
  words = [words[i] for i in non_punct]
  counts = [counts[i] for i in non_punct]
  poss = [poss[i] for i in non_punct]

  vocab = {'words': words, 'counts': counts, 'poss': poss};
  return vocab
