# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 15:27:36 2019

@author: Minjun Park

"""

import re, collections
from os import listdir, mkdir
from os.path import isfile, join

FRAME = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
html, body {
            margin: 0px;
            padding: 0px;
            width: 100%;
            height: 100%;
            overflow: hidden;
            text-align: center;
            font-family: Helvetica;
        }

        #tree {
            width: 100%;
            height: 100%;
        }

        .highlight rect{
            fill: #F57C00 !important;
        }
</style>
<script src="https://balkangraph.com/js/latest/OrgChart.js"></script>

</head>

<body>
<div style="width:100%; height:700px;" id="tree"/>
<script>

		OrgChart.templates.sentence = Object.assign({}, OrgChart.templates.ana);
        OrgChart.templates.sentence.size = [520, 120];
        OrgChart.templates.sentence.field_0 = '<text class="field_0"  style="font-size: 24px;" fill="#ffffff" x="260" y="90" text-anchor="middle">{val}</text>';
        OrgChart.templates.sentence.field_1 = '<text class="field_1"  style="font-size: 20px;" fill="#ffffff" x="500" y="30" text-anchor="end">{val}</text>';
        OrgChart.templates.sentence.node = '<rect x="0" y="0" height="120" width="520" fill="#039BE5" stroke-width="1" stroke="#aeaeae" rx="5" ry="5"></rect>';
        OrgChart.templates.ana.field_1 = '<text width="145" text-overflow="multiline" style="font-size: 20px;" fill="#ffffff" x="200" y="30" text-anchor="end">{val}</text>';

		var chart = new OrgChart(document.getElementById("tree"), {
                nodeBinding: {
                    field_0: "type",
                    field_1: "text"                    
                },
                orientation: BALKANGraph.orientation.top_left,
                tags: {
                    "sentence": {
                        template: "sentence"
                    },
                    "hide": {
                        state: OrgChart.COLLAPSE
                    }
                },
                nodes: [ 
                ]
            });

            var nodeEelements = chart.getNodeElements();
            for (var i = 0; i < nodeEelements.length; i++) {
                nodeEelements[i].addEventListener("mouseover", function () {
                    this.classList.add("highlight");
                    var nodeId = this.getAttribute("node-id");
                    var parent = chart.nodes[nodeId].parent;
                    if (parent != null) {
                        chart.getNodeElement(parent.id).classList.add("highlight");
                    }
                });

                nodeEelements[i].addEventListener("mouseleave", function () {
                    this.classList.remove("highlight");
                    var nodeId = this.getAttribute("node-id");
                    var parent = chart.nodes[nodeId].parent;
                    if (parent != null) {
                        chart.getNodeElement(parent.id).classList.remove("highlight");
                    }
                });
            }
    </script>

</body>
</html>
'''
TAGMAP = {
        'advs':'부사어',
        'adv': '부사어',
        'att': '관형어',
        'cmp': '보어',
        'cmp1': '보어1',
        'cmp2': '보어2',
        'dl': '독립성분',
        'hed': '중심어',
        'heda': '(부사어의)중심어',
        'hedb': '(관형어의)중심어',
        'hedc': '(보어의)중심어',
        'obj': '목적어',
        'obji': '간접목적어',
        'obsbj': '목적어주어',
        'prd': '술어',
        'prd1': '대술어',
        'prd2': '소술어',
        'prda': '술어a',
        'prdb': '술어b',
        'prdc': '술어c',
        'sbj': '주어',
        'sbj1': '대주어',
        'sbj2': '소주어',
        'v': '술어동사'
        }

def file2vocabtable(fname):
    '''
    read a TSV file and converts to a vocab table:
    {(#, token): [ phrase[1], phrase[2], phrase[3], ...]}
    '''
    # read a TSV file
    # -> {(1, '\ufeff咱们'): 'sbj', (2, '有'): 'prd[1]|prda[2]|v[3]',...}
    data = {}
    with open(fname, encoding='UTF8') as f:
        line = f.readline()
        while re.search(r'\#Text\=', line) == None:
            line = f.readline()
        sentence = re.findall(r'(?<=\#Text\=).*$', line)
        sentence = ''.join(sentence)
        head = (r'{{ id: 0, text: "{}", type: "SENTENCE", tags: ["sentence"] }},'.format(sentence))
        # after the 'sentence' line: 
        line = f.readline()
        # accumulate information of every words
        while line != '':
            data.update(split_fields(line))
            line = f.readline()
    return data, head

def split_fields(line):
    # line의 정보를 나누고 추리기
    # ['1-1', '0-3', '\ufeff咱们', 'sbj'] -> {(1, '\ufeff咱们'): ['sbj']}
    # defaultdict 필요없음 dict.setdefault로 가능.
    t = line.split('\t')
    key_head = int(re.findall(r'(?<=1-)\d',t[0])[0])
    if key_head == None: raise ValueError
    key_tail = t[2]
    if key_tail == None: raise ValueError
    value = t[3]
    if value == None: raise ValueError
    d = {}
    d.setdefault((key_head, key_tail), value.split('|'))
    
    return d

class OrderedDefaultdict(collections.OrderedDict):
    """ A defaultdict with OrderedDict as its base class. """

    def __init__(self, default_factory=None, *args, **kwargs):
        if not (default_factory is None
                or isinstance(default_factory, collections.Callable)):
            raise TypeError('first argument must be callable or None')
        super(OrderedDefaultdict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory  # called by __missing__()

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key,)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):  # optional, for pickle support
        args = (self.default_factory,) if self.default_factory else tuple()
        return self.__class__, args, None, None, self.iteritems()

    def __repr__(self):  # optional
        return '%s(%r, %r)' % (self.__class__.__name__, self.default_factory,
                               list(self.iteritems()))

def getNodeTable(vocab_table):
    '''from vocab:phrase pairs, induce phrase:vocab pairs.
    {(1, '\ufeff咱们'): ['sbj']} -> {'sbj': [(1, '\ufeff咱们')]}'''
    d = OrderedDefaultdict(list)
    for k,v in vocab_table.items():
        for phrase in v:
            d[phrase].append(k)
    return d

def findParentName(vocab_table, target_phrase):
    ''' findParentName(a, 'sbj') -> 'root'
        findParentName(a, 'prda[2]') -> 'prd[1]'
        findParentName(a, 'non-exist')-> NoneType''' 
    for dependency in vocab_table.values():
        # ['prd[1]', 'prda[2]', 'v[3]']
        try:
            location = dependency.index(target_phrase)
            if location != 0:
                return dependency[location-1]
            else: return 'root'
        except ValueError:
            continue

def get_pid(node_id, vocab_table, node_table):
    '''node_id: 0 is sentence, 1~n is each token.'''
    if node_id == 0:
        print('>>>input node_id must be larger than 0<<<')
        raise ValueError
    orderedPhraselist = ['root'] + list(node_table.keys())
    # ['root', 'token1', 'token2', ...]
    target_phrase_name = orderedPhraselist[node_id]
    parent_phrase_name = findParentName(vocab_table, target_phrase_name)
    pid = orderedPhraselist.index(parent_phrase_name)
    return pid

def formatter(node_id, pid, text, phrase_name):
    return r'{{ id: {0}, pid: {1}, text: "{2}", type: "{3}", tags: ["hide"] }},'.format\
(node_id, pid, text, maps2kr(phrase_name))

def maps2kr(phrase_name):
    '''adjusting keys, eg. sbj[1] -> sbj, v.[5] -> v, oov -> oov, ""->""
    mapping to kr, eg. 주어, 술어동사, None, ERROR'''
    try:
        k = re.findall(r'[a-z12]+', phrase_name)[0]
        kr = TAGMAP.get(k)
        return kr
    except:
        return 'ERROR'

def jsconverter(node_table, vocab_table):
    for i, phrase in enumerate(node_table.keys(), start=1):
        idx = i # node_id
        pid = get_pid(idx, vocab_table, node_table)
        text = ' '.join([tok for (no, tok) in node_table.get(phrase)])
        phrase_name = phrase
        
        yield (formatter(idx, pid, text, phrase_name))

if __name__ == '__main__':
    print('TSV to HTML')
##    # empty slot
##    with open('frame.html', encoding='UTF8') as handle:
##            frame = handle.read()
    # create dir
    try:
        mkdir('temp')
    except FileExistsError:
        pass
    # Batch process
    filelist = [f for f in listdir('.') if f.endswith('.tsv')]
#    filelist = ['jc_sp_01_000.tsv']
    for f in filelist:
        print('processing {} ...'.format(f), end='')
        vocab_table, head = file2vocabtable(f)
        node_table = getNodeTable(vocab_table)
        content = head+'\n'+'\n'.join(jsconverter(node_table, vocab_table))
        html = re.sub(r'(?<=nodes: \[)\s', '\n'+content, FRAME)
        # write to html
        ftname = f.split('.')[0]
        with open('./temp/{}.html'.format(ftname), 'w', encoding='UTF8') as handle:
            handle.write(html)
        print(' succeed.')


#    filelist = [f for f in listdir('./corpus') if isfile(join('./corpus', f))]
#    for f in filelist:
#        print(f)
#        vocab_table = file2vocabtable('./corpus/'+f)
#        node_table = getNodeTable(vocab_table)
#        jsconverter(node_table, vocab_table)
